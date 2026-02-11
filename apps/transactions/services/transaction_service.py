from decimal import Decimal
from apps.transactions.models import Transaction
from django.db import transaction
import csv
from io import StringIO
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from collections import defaultdict
from datetime import datetime, timedelta

from django.db import transaction as db_transaction
from apps.transactions.models import Transaction
from apps.activity.utils import log_activity


def calculate_user_balance(user):
    earned = Transaction.objects.filter(
        user=user,
        transaction_type='EARNED'
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    
    purchased = Transaction.objects.filter(
        user=user,
        transaction_type='PURCHASED'
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    
    return earned - purchased


def create_transaction(user, transaction_type, amount, description=''):
    from apps.users.models import Balance

    with transaction.atomic():
        txn = Transaction.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            description=description
        )

        balance = user.balance
        if transaction_type == 'EARNED':
            balance.amount += amount
        elif transaction_type == 'PURCHASED':
            balance.amount -= amount
        balance.save()
    return txn

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
    transactions = Transaction.objects.filter(user=user)

    total_credit = transactions.filter(transaction_type='EARNED').aggregate(Sum('amount'))['amount__sum'] or 0
    total_debit = transactions.filter(transaction_type='PURCHASED').aggregate(Sum('amount'))['amount__sum'] or 0

    # Monthly trend
    monthly = transactions.annotate(month=TruncMonth('created_at')).values('month', 'transaction_type').annotate(total=Sum('amount'))

    trend = defaultdict(lambda: {'EARNED': 0, 'PURCHASED': 0})
    for item in monthly:
        month_str = item['month'].strftime('%Y-%m')
        trend[month_str][item['transaction_type']] = item['total']

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
        trend.setdefault(month_str, {'EARNED': 0, 'PURCHASED': 0})
        trend[month_str][item['transaction_type']] = item['total']

    last_3_months = sorted(trend.keys())[-3:]
    earned_avg = sum(trend[m]['EARNED'] for m in last_3_months) / 3 if last_3_months else 0
    purchased_avg = sum(trend[m]['PURCHASED'] for m in last_3_months) / 3 if last_3_months else 0

    return {
        "predicted_earned": earned_avg,
        "predicted_purchased": purchased_avg,
        "predicted_balance_change": earned_avg - purchased_avg
    }





def create_transaction(user, transaction_type, amount, description=''):
    from apps.users.models import Balance

    with db_transaction.atomic():
        txn = Transaction.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            description=description
        )

        balance = user.balance
        if transaction_type == 'EARNED':
            balance.amount += amount
        else:
            balance.amount -= amount
        balance.save()

        # 👇 ACTIVITY LOG
        log_activity(
            user=user,
            activity_type='TRANSACTION',
            message=f"{transaction_type} of {amount}",
            metadata={
                "transaction_id": txn.id,
                "amount": str(amount)
            }
        )

    return txn