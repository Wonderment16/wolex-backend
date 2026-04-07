from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import BillingAccount, Balance
from apps.transactions.models import Transaction
from apps.statements.models import BankStatement
from apps.users.plan import get_pricing_ngn

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "password"]
        read_only_fields = ["id"]

    def validate_password(self, value):
        validate_password(value, self.instance)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data, password=password)
        # create related profile/settings automatically (signals could be used but we keep explicit)
        from apps.profiles.models import Profile, Settings
        Profile.objects.get_or_create(user=user)
        Settings.objects.get_or_create(user=user)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data["name"] = user.first_name
        profile_completed = getattr(user, 'profile_completed', False)
        data.update({
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_completed": profile_completed,
                "email_verified": user.email_verified,
            }
        })
        return data


class UserContextSerializer(serializers.Serializer):
    email = serializers.EmailField()
    balance = serializers.DecimalField(
        source='Balance.amount', 
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    profile_completed = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()

    recent_transactions = serializers.SerializerMethodField()
    statement_insights = serializers.SerializerMethodField()

    def get_profile_completed(self, user):
        try:
            return bool(user.profile.is_complete)
        except Exception:
            return False

    def get_email_verified(self, user):
        return bool(user.email_verified)

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


class BillingAccountSerializer(serializers.ModelSerializer):
    amount_ngn = serializers.IntegerField(read_only=True)

    class Meta:
        model = BillingAccount
        fields = [
            "id",
            "account_name",
            "account_number",
            "bank_name",
            "account_type",
            "amount_ngn",
            "verified",
            "created_at",
        ]
        read_only_fields = ["id", "amount_ngn", "verified", "created_at"]

    def validate_account_number(self, value):
        normalized = value.strip().replace(" ", "")
        if not normalized.isdigit():
            raise serializers.ValidationError("Account number must contain only digits.")
        if len(normalized) < 6 or len(normalized) > 20:
            raise serializers.ValidationError("Account number length looks invalid.")
        return normalized

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")
        account_type = validated_data.get("account_type")
        amount_ngn = get_pricing_ngn(account_type)
        return BillingAccount.objects.create(
            user=user,
            amount_ngn=amount_ngn,
            **validated_data,
        )
