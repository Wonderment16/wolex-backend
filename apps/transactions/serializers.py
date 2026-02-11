from rest_framework import serializers
from apps.transactions.models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'amount', 'description', 'created_at', 'category']
        read_only_fields = ['id', 'created_at']

class TransactionSummarySerializer(serializers.Serializer):
    total_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_purchased = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)

def validate_amount(self, value):
    if value <= 0:
        raise serializers.ValidationError("Amount must be greater than zero.")
    return value

def validate_transaction_type(self, value):
    allowed = ['EARNED', 'PURCHASED']
    if value not in allowed:
        raise serializers.ValidationError(f"Invalid transaction type.")
    return value
