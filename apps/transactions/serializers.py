from rest_framework import serializers
from apps.transactions.models import Transaction
from apps.category.models import Category
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

from apps.transactions.currency import (
    CurrencyValidationError,
    enforce_currency_limit,
    get_user_currency,
    normalize_currency,
    resolve_workspace,
    validate_currency_code,
)


class TransactionSerializer(serializers.ModelSerializer):
    # 1. Change this to a SerializerMethodField so it uses your get_category logic below
    category = serializers.SerializerMethodField(read_only=True) 
    category_id = serializers.IntegerField(write_only=True, required=False)
    workspace_id = serializers.IntegerField(write_only=True, required=False)
    workspace = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id", "transaction_type", "amount", "description",
            "currency", "created_at",
            "category", "category_id",
            "client_id", "version", 
            "updated_at", "deleted_at",
            "workspace", "workspace_id",
        ]

    def get_workspace(self, obj):
        if obj.workspace_id:
            return {"id": obj.workspace_id, "name": obj.workspace.name}
        return None


    def get_category(self, obj):
        if obj.category_fk:
            return {
                "id": obj.category_fk.id,
                "name": obj.category_fk.name,
                "code": obj.category_fk.code,
                "kind": obj.category_fk.kind
            }

        # Safe fallback: If no category exists, return a default object 
        # instead of trying to access properties on a None object.
        return {
            "id": None,
            "name": "Uncategorized",
            "code": "N/A",
            "kind": "N/A"
        }

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        attrs = super().validate(attrs)
        
        category_id = self.initial_data.get("category_id")
        transaction_type = attrs.get("transaction_type")

        cat = None

        if category_id:
            cat = Category.objects.filter(id=category_id).first()

        if not cat:
            raise serializers.ValidationError({"category_id": "Invalid category_id"})
        if cat.kind != transaction_type:
            raise serializers.ValidationError({
                "category_id": f"{cat.name} is not valid for {transaction_type}"
            })
        
        currency = attrs.get("currency")
        if currency is None:
            if self.instance and getattr(self.instance, "currency", None):
                currency = self.instance.currency
            else:
                currency = get_user_currency(user)
            attrs["currency"] = currency

        try:
            currency = validate_currency_code(currency)
        except CurrencyValidationError as exc:
            raise serializers.ValidationError({"currency": str(exc)})

        attrs["currency"] = normalize_currency(currency)

        workspace_id = None
        if hasattr(self, "initial_data"):
            workspace_id = self.initial_data.get("workspace_id")
        if self.context.get("workspace_id"):
            workspace_id = self.context.get("workspace_id")

        workspace = resolve_workspace(user, workspace_id)
        if not self.instance or currency != getattr(self.instance, "currency", None):
            try:
                enforce_currency_limit(user, workspace, currency, instance=self.instance)
            except CurrencyValidationError as exc:
                raise serializers.ValidationError({"currency": str(exc)})

        return attrs

    def validate_transaction_type(self, value):
        normalized = value.upper()
        if normalized == "EXPENSES":
            normalized = "EXPENSE"
        allowed = {choice[0] for choice in Transaction.TRANSACTION_TYPES}
        if normalized not in allowed:
            raise serializers.ValidationError("Invalid transaction type.")
        return normalized

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid category_id")
        return value

    def _apply_category_id(self, txn, category_id):
        if category_id is None:
            return
        cat = Category.objects.get(id=category_id)
        txn.category_fk_id = category_id
        txn.save(update_fields=["category_fk_id"])

    def create(self, validated_data):
        category_id = validated_data.pop("category_id", None)
        txn = super().create(validated_data)
        self._apply_category_id(txn, category_id)
        return txn


    def update(self, instance, validated_data):
    # normal update
        instance = super().update(instance, validated_data)

        # bump version every update
        instance.version += 1
        instance.save(update_fields=["version"])

        return instance