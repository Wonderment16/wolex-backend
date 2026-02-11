from rest_framework import serializers
from apps.users.models import User
from apps.transactions.models import Transaction
from apps.statements.models import BankStatement

class UserContextSerializer(serializers.Serializer):
    email = serializers.EmailField()
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)

    recent_transactions = serializers.SerializerMethodField()
    statement_insights = serializers.SerializerMethodField()

    def get_recent_transactions(self, user):
        transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:5]
        return [
            {
                "type": t.transaction_type,
                "amount": t.amount,
                "description": t.description,
                "date": t.created_at
            }
            for t in transactions
        ]

    def get_statement_insights(self, user):
        latest_statement = BankStatement.objects.filter(
            user=user,
            processed=True,
        ).order_by("-uploaded_at").first()

        return latest_statement.analysis_result if latest_statement else None
