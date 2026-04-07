from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, Settings

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    """Read-only/basic serializer for profile data."""

    class Meta:
        model = Profile
        fields = [
            "phone",
            "bio",
            "avatar",
            "middle_name",
            "date_of_birth",
            "profession",
            "nationality",
            "account_type",
            "is_complete",
        ]
        read_only_fields = ["is_complete"]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer used for patching profile; also updates user fields."""

    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    # middle_name already on profile and included automatically

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "phone",
            "bio",
            "avatar",
            "middle_name",
            "date_of_birth",
            "profession",
            "nationality",
            "account_type",
        ]

    def update(self, instance, validated_data):
        # pop user fields out and set on user
        user = instance.user
        for attr in ("first_name", "last_name"):
            if attr in validated_data:
                setattr(user, attr, validated_data.pop(attr))
        user.save()

        # nationality -> auto currency mapping handled in view
        profile = super().update(instance, validated_data)

        # recompute completion flag
        profile.is_complete = bool(
            profile.user.first_name and profile.last_name and profile.account_type and profile.nationality
        )
        profile.save()
        return profile


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ["currency", "notifications_enabled", "theme"]

