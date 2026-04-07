from datetime import date, timedelta
import calendar

from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth, TruncWeek, Coalesce, ExtractWeekDay, ExtractDay, ExtractMonth
from django.utils import timezone
from django.utils.timezone import now
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage
from decimal import Decimal
from django.db import models

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from apps.core.permissions import IsOwner
from apps.transactions.models import Transaction, Budget
from apps.transactions.serializers import TransactionSerializer
from apps.transactions.services.transaction_service import create_transaction, export_transactions_csv, dashboard_data
from apps.workspaces.models import Workspace
from apps.transactions.currency import get_user_currency
from rest_framework import status

# Create your views here.

INCOME_TYPES = ["INCOME"]
EXPENSE_TYPES = ["EXPENSE"]


class TransactionSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total_earned = user.transactions.filter(transaction_type__in=INCOME_TYPES, deleted_at__isnull=True).aggregate(Sum('amount'))['amount__sum'] or 0
        total_purchased = user.transactions.filter(transaction_type__in=EXPENSE_TYPES, deleted_at__isnull=True).aggregate(Sum('amount'))['amount__sum'] or 0
        balance = total_earned - total_purchased

        return Response({
            'total_earned': total_earned,
            'total_purchased': total_purchased,
            'balance': balance
        })
    
class MonthlySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        current_year = now().year

        monthly_earned = user.transactions.filter(
            transaction_type__in=INCOME_TYPES,
            created_at__year=current_year,
            deleted_at__isnull=True
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('amount')).order_by('month')

        monthly_purchased = user.transactions.filter(
            transaction_type__in=EXPENSE_TYPES,
            created_at__year=current_year,
            deleted_at__isnull=True
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('amount')).order_by('month')

        return Response({
            'monthly_earned': list(monthly_earned),
            'monthly_purchased': list(monthly_purchased)
        })

class WeeklySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        current_year = now().year

        weekly_earned = user.transactions.filter(
            transaction_type__in=INCOME_TYPES,
            created_at__year=current_year,
            deleted_at__isnull=True
        ).annotate(week=TruncWeek('created_at')).values('week').annotate(total=Sum('amount')).order_by('week')

        weekly_purchased  = user.transactions.filter(
            transaction_type__in=EXPENSE_TYPES,
            created_at__year=current_year,
            deleted_at__isnull=True
        ).annotate(week=TruncWeek('created_at')).values('week').annotate(total=Sum('amount')).order_by('week')

        return Response({
            'weekly_earned': list(weekly_earned),
            'weekly_purchased': list(weekly_purchased)
        })

class CategorySummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        base_qs = user.transactions.filter(deleted_at__isnull=True)

        expense_summary = base_qs.filter(
            transaction_type="EXPENSE"
        ).values("category_fk__name", "category_fk__code").annotate(
            total=Sum("amount")
        ).order_by("-total")

        income_summary = base_qs.filter(
            transaction_type="INCOME"
        ).values("category_fk__name", "category_fk__code").annotate(
            total=Sum("amount")
        ).order_by("-total")

        return Response({
            "expense_categories": expense_summary,
            "income_categories": income_summary
        })


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        income_types = INCOME_TYPES
        expense_types = EXPENSE_TYPES
        currency = get_user_currency(request.user)


        personal = Workspace.objects.filter(created_by=request.user, name="Personal").first()

        qs = Transaction.objects.filter(
            user=request.user,
            workspace=personal,
            deleted_at__isnull=True
        )
        workspace_id = request.query_params.get("workspace_id")
        if workspace_id:
            qs = qs.filter(workspace_id=workspace_id)

        def to_float(value):
            if value is None:
                return 0.0
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        totals = qs.aggregate(
            total_income=Coalesce(
                Sum("amount", filter=Q(transaction_type__in=income_types)), 
                Decimal('0.00'), # Changed from 0
                output_field=models.DecimalField()
            ),
            total_expense=Coalesce(
                Sum("amount", filter=Q(transaction_type__in=expense_types)), 
                Decimal('0.00'), # Changed from 0
                output_field=models.DecimalField()
            ),
        )

        top_expense = (
            qs.filter(transaction_type__in=expense_types, deleted_at__isnull=True)
            .values("category_fk__name", "category_fk__code")
            .annotate(total=Sum("amount"))
            .order_by("-total")
            .first()
        )

        top_income = (
            qs.filter(transaction_type__in=income_types, deleted_at__isnull=True)
            .values("category_fk__name", "category_fk__code")
            .annotate(total=Sum("amount"))
            .order_by("-total")
            .first()
        )

        insights = []

        if totals["total_expense"] > totals["total_income"]:
            insights.append("⚠️ You are spending more than you earn.")

        if totals["total_income"] > 0:
            savings_rate = float((totals["total_income"] - totals["total_expense"]) / totals["total_income"])
            if savings_rate > 0.3:
                insights.append("🔥 Great job! You are saving over 30% of your income.")
            elif savings_rate < 0.1:
                insights.append("⚠️ Your savings rate is low. Consider reducing expenses.")

        # Inside DashboardView's get method, look for the insights logic:
        if top_expense and top_expense.get('category'): # Add 'and top_expense.get('category')'
            insights.append(f"💡 Your biggest expense is {top_expense['category']}.")

        if top_income and top_income.get('category'): # Add this check too
            insights.append(f"💡 Your biggest income source is {top_income['category']}.")

        balance = totals["total_income"] - totals["total_expense"]

        

        page = int(request.query_params.get("last_page", 1))
        page_size = int(request.query_params.get("last_page_size", 5))

        # Use 'category__name' (or whatever the field is in your Category model)
        last_qs = qs.order_by("-created_at").values(
            "id", "amount", "transaction_type", "category_fk__name", "created_at", "description"
        )
        paginator = Paginator(last_qs, page_size)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages) if paginator.num_pages else []

        last_transactions = []
        if page_obj:
            for row in page_obj.object_list:
                last_transactions.append({
                    "id": row["id"],
                    "amount": to_float(row["amount"]),
                    "transaction_type": row["transaction_type"],
                    "category_name": row["category_fk__name"] or "Miscellaneous", # Use the __name value
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "description": row["description"],
                })

        today = timezone.localdate()
        sunday_offset = (today.weekday() + 1) % 7  # Sunday=0
        week_start = today - timedelta(days=sunday_offset)
        week_end = week_start + timedelta(days=6)

        week_qs = qs.filter(
            created_at__date__range=(week_start, week_end),
            deleted_at__isnull=True
        ).annotate(
            weekday=ExtractWeekDay("created_at")  # 1=Sunday ... 7=Saturday
        )

        weekly_income = [0.0] * 7
        weekly_expense = [0.0] * 7

        for row in week_qs.values("weekday", "transaction_type").annotate(total=Sum("amount")):
            idx = row["weekday"] - 1
            if row["transaction_type"] in income_types:
                weekly_income[idx] = to_float(row["total"])
            elif row["transaction_type"] in expense_types:
                weekly_expense[idx] = to_float(row["total"])

        weekly = {
            "labels": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            "datasets": [
                {"label": "Income", "data": weekly_income},
                {"label": "Expense", "data": weekly_expense},
            ],
        }

        month_start = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)

        month_qs = qs.filter(
            created_at__year=today.year,
            created_at__month=today.month,
            deleted_at__isnull=True
        ).annotate(
            day=ExtractDay("created_at")
        )

        monthly_income = [0.0] * 4
        monthly_expense = [0.0] * 4

        for row in month_qs.values("day", "transaction_type").annotate(total=Sum("amount")):
            week_of_month = min(4, int((row["day"] - 1) // 7) + 1)
            idx = week_of_month - 1
            if row["transaction_type"] in income_types:
                monthly_income[idx] = to_float(row["total"])
            elif row["transaction_type"] in expense_types:
                monthly_expense[idx] = to_float(row["total"])

        monthly = {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "datasets": [
                {"label": "Income", "data": monthly_income},
                {"label": "Expense", "data": monthly_expense},
            ],
        }

        year_start = date(today.year, 1, 1)
        year_end = date(today.year, 12, 31)

        year_qs = qs.filter(
            created_at__date__range=(year_start, year_end),
            deleted_at__isnull=True
        ).annotate(
            month=ExtractMonth("created_at")
        )

        yearly_income = [0.0] * 12
        yearly_expense = [0.0] * 12

        for row in year_qs.values("month", "transaction_type").annotate(total=Sum("amount")):
            idx = row["month"] - 1
            if row["transaction_type"] in income_types:
                yearly_income[idx] = to_float(row["total"])
            elif row["transaction_type"] in expense_types:
                yearly_expense[idx] = to_float(row["total"])

        yearly = {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "datasets": [
                {"label": "Income", "data": yearly_income},
                {"label": "Expense", "data": yearly_expense},
            ],
        }

        print("TOTAL TXNS:", qs.count())
        print("MONTHLY INCOME:", monthly_income)
        print("MONTHLY EXPENSE:", monthly_expense)

        return Response({
            "balance": to_float(balance),
            "total_income": to_float(totals["total_income"]),
            "total_expense": to_float(totals["total_expense"]),
            "monthly": monthly,
            "weekly": weekly,
            "yearly": yearly,
            "last_transactions": last_transactions,
            "last_transactions_pagination": {
                "page": page,
                "page_size": page_size,
                "count": paginator.count if hasattr(paginator, "count") else 0,
                "pages": paginator.num_pages if hasattr(paginator, "num_pages") else 0,
            },
            "top_category": top_expense["category_fk__name"] if top_expense else "N/A", 
            "top_income_source": top_income["category_fk__name"] if top_income else "N/A",


            "insights": insights,
            'currency': currency,   
        })





class TransactionViewSet(ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Transaction.objects.all()   # <-- ADD THIS LINE

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(
            user=user,
            deleted_at__isnull=True
        )
        workspace_id = self.request.query_params.get("workspace_id")
        category = self.request.query_params.get("category_fk__code")
        search = self.request.query_params.get("search")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")


        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        else:
            personal = Workspace.objects.filter(created_by=user, name="Personal").first()
            if personal:
                queryset = queryset.filter(workspace=personal)

        # THEN APPLY FILTERS
        if category:
            queryset = queryset.filter(category=category)

        if search:
            queryset = queryset.filter(description__icontains=search)

        if start_date and end_date:
            queryset = queryset.filter(created_at__date__range=[start_date, end_date])

        return queryset.order_by("-created_at")        


    
    def perform_create(self, serializer):
        user = self.request.user
        workspace_id = self.request.data.get("workspace_id")

        if workspace_id:
            serializer.save(user=user, workspace_id=workspace_id)
            return

        personal, created = Workspace.objects.get_or_create(created_by=user, name="Personal")
        serializer.save(user=user, workspace=personal)


    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export_csv(self, request):
        csv_file = export_transactions_csv(request.user)
        response = HttpResponse(csv_file, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        return response

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        data = dashboard_data(request.user)
        last_txns = data.get('last_transactions', [])
        serializer = TransactionSerializer(last_txns, many=True)

        data["last_transactions"] = serializer.data
        return Response(data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = timezone.now()
        instance.version += 1
        instance.save(update_fields=["deleted_at", "version"])
        
        return Response(status=status.HTTP_204_NO_CONTENT)



class FinancialSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        total_earned = user.transactions.filter(
            transaction_type__in=INCOME_TYPES,
            deleted_at__isnull=True
            ).aggregate(Sum('amount'))['amount__sum'] or 0

        total_purchased = user.transactions.filter(
            transaction_type__in=EXPENSE_TYPES,
            deleted_at__isnull=True
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        return Response({
            'balance': user.balance.amount,
            'total_earned': total_earned,
            'total_purchased': total_purchased
        })