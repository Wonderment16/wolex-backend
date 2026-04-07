from decimal import Decimal
import csv
from io import StringIO
from collections import defaultdict

from django.db import transaction as db_transaction
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from apps.transactions.models import Transaction
from apps.activity.utils import log_activity


def normalize_transaction_type(value):
    if value is None:
        return value
    normalized = value.upper()
    if normalized == "EXPENSES":
        return "EXPENSE"
    return normalized


def calculate_user_balance(user):
    income_types = ["INCOME"]
    expense_types = ["EXPENSE"]

    earned = Transaction.objects.filter(
        user=user,
        transaction_type__in=income_types,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    purchased = Transaction.objects.filter(
        user=user,
        transaction_type__in=expense_types,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    return earned - purchased


def export_transactions_csv(user):
    transactions = Transaction.objects.filter(user=user).order_by("-created_at")

    csv_file = StringIO()
    writer = csv.writer(csv_file)

    # Header
    writer.writerow(["Date", "Type", "Amount", "Description"])

    for txn in transactions:
        writer.writerow([
            txn.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            txn.transaction_type,
            str(txn.amount),
            txn.description or ""
        ])

    csv_file.seek(0)
    return csv_file


def dashboard_data(user):
    income_types = ["INCOME"]
    expense_types = ["EXPENSE"]

    transactions = Transaction.objects.filter(user=user)

    total_credit = transactions.filter(transaction_type__in=income_types).aggregate(Sum('amount'))['amount__sum'] or 0
    total_debit = transactions.filter(transaction_type__in=expense_types).aggregate(Sum('amount'))['amount__sum'] or 0

    # Monthly trend
    monthly = transactions.annotate(month=TruncMonth('created_at')).values('month', 'transaction_type').annotate(total=Sum('amount'))

    trend = defaultdict(lambda: {'INCOME': 0, 'EXPENSE': 0})
    for item in monthly:
        month_str = item['month'].strftime('%Y-%m')
        normalized = normalize_transaction_type(item['transaction_type'])
        if normalized in trend[month_str]:
            trend[month_str][normalized] = item['total']

    last_transactions = transactions.order_by('-created_at')[:5]

    return {
        'current_balance': user.balance.amount,
        'total_earned': total_credit,
        'total_purchased': total_debit,
        'monthly_trend': trend,
        'last_transactions': last_transactions
    }


def predict_next_month_flow(user):
    from django.db.models.functions import TruncMonth
    transactions = Transaction.objects.filter(user=user)

    monthly = transactions.annotate(month=TruncMonth('created_at')) \
        .values('month', 'transaction_type') \
        .annotate(total=Sum('amount'))
    
    trend = {}
    for item in monthly:
        month_str = item["month"].strftime("%Y-%m")
        trend.setdefault(month_str, {'INCOME': 0, 'EXPENSE': 0})
        normalized = normalize_transaction_type(item['transaction_type'])
        if normalized in trend[month_str]:
            trend[month_str][normalized] = item['total']

    last_3_months = sorted(trend.keys())[-3:]
    earned_avg = sum(trend[m]['INCOME'] for m in last_3_months) / 3 if last_3_months else 0
    purchased_avg = sum(trend[m]['EXPENSE'] for m in last_3_months) / 3 if last_3_months else 0

    return {
        "predicted_earned": earned_avg,
        "predicted_purchased": purchased_avg,
        "predicted_balance_change": earned_avg - purchased_avg
    }


def create_transaction(user, transaction_type, amount, description=''):
    from apps.users.models import Balance

    with db_transaction.atomic():
        normalized_type = normalize_transaction_type(transaction_type)
        txn = Transaction.objects.create(
            user=user,
            transaction_type=normalized_type,
            amount=amount,
            description=description
        )

        balance = user.balance
        if normalized_type == 'INCOME':
            balance.amount += amount
        else:
            balance.amount -= amount
        balance.save()

        # 👇 ACTIVITY LOG
        log_activity(
            user=user,
            activity_type='TRANSACTION',
            message=f"{normalized_type} of {amount}",
            metadata={
                "transaction_id": txn.id,
                "amount": str(amount)
            }
        )

    return txn
