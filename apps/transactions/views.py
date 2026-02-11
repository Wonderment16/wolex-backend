from django.shortcuts import render
from rest_framework import viewsets, permissions
from apps.transactions.serializers import TransactionSerializer
from apps.transactions.models import Transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils.timezone import now
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Transaction
from .serializers import TransactionSerializer
from apps.core.permissions import IsOwner
from apps.transactions.services.transaction_service import create_transaction
from django.http import HttpResponse
from apps.transactions.services.transaction_service import export_transactions_csv
from rest_framework.decorators import action
from apps.transactions.services.transaction_service import dashboard_data


# Create your views here.


class TransactionSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total_earned = user.transactions.filter(transaction_type='EARNED').aggregate(Sum('amount'))['amount__sum'] or 0
        total_purchased = user.transactions.filter(transaction_type='PURCHASED').aggregate(Sum('amount'))['amount__sum'] or 0
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
            transaction_type='EARNED',
            created_at__year=current_year
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('amount')).order_by('month')

        monthly_purchased = user.transactions.filter(
            transaction_type='PURCHASED',
            created_at__year=current_year
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
            transaction_type='EARNED',
            created_at__year=current_year
        ).annotate(week=TruncWeek('created_at')).values('week').annotate(total=Sum('amount')).order_by('week')

        weekly_purchased  = user.transactions.filter(
            transaction_type='PURCHASED',
            created_at__year=current_year
        ).annotate(week=TruncWeek('created_at')).values('week').annotate(total=Sum('amount')).order_by('week')

        return Response({
            'weekly_earned': list(weekly_earned),
            'weekly_purchased': list(weekly_purchased)
        })

class CategorySummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        category_summary = user.transactions.values('category').annotate(
            total=Sum('amount')).order_by('-total')
        return Response(category_summary)



class TransactionViewSet(ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        user = self.request.user
        data = serializer.validated_data

        create_transaction(
            user=user,
            transaction_type=data['transaction_type'],
            amount=data['amount'],
            description=data.get('description', '')
        )

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


class FinancialSummaryView(APIView):
    permission_class = [IsAuthenticated]

    def get(self, request):
        user = request.user

        total_earned = user.transactions.filter(
            transaction_type='EARNED'
            ).aggregate(Sum('amount'))['amount__sum'] or 0

        total_purchased = user.transactions.filter(
            transaction_type='PURCHASED'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        return Response({
            'balance': user.balance.amount,
            'total_earned': total_earned,
            'total_purchased': total_purchased
        })