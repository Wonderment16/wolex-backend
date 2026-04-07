from rest_framework import serializers
from apps.transactions.models import Transaction

from apps.transactions.currency import (
    CurrencyValidationError,
    enforce_currency_limit,
    get_user_currency,
    normalize_currency,
    resolve_workspace,
    validate_currency_code,
)


class SyncTransactionSerializer(serializers.ModelSerializer):
    """
    Used for sync push/pull, not normal CRUD.
    """

    class Meta:
        model = Transaction
        fields = [
            "client_id",
            "version",
            "transaction_type",
            "amount",
            "currency",
            "description",
            "category",      # ✅ string category
            "workspace",     # ok to include; we'll lock it down as read-only
            "updated_at",
            "deleted_at",
        ]

        extra_kwargs = {
            "version": {"required": False},
            "updated_at": {"required": False},
            "deleted_at": {"required": False, "allow_null": True},
            "category": {"required": False},  # client can omit, model default kicks in
            "currency": {"required": False},
            "workspace": {"required": False, "allow_null": True},
        }

        read_only_fields = [
            "workspace",     # ✅ don’t let client switch workspace via payload
            "updated_at",    # ✅ server controls timestamps
        ]

    def validate_category(self, value):
        """
        Since you're using a CharField with choices on Transaction,
        this makes sure client can't send nonsense.
        """
        allowed = {c[0] for c in Transaction.CATEGORY_CHOICES}
        if value not in allowed:
            raise serializers.ValidationError("Invalid category.")
        return value


    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_transaction_type(self, value):
        normalized = value.upper()
        if normalized == "EXPENSES":
            normalized = "EXPENSE"
        allowed = {"INCOME", "EXPENSE"}
        if normalized not in allowed:
            raise serializers.ValidationError("Invalid transaction type.")
        return normalized
