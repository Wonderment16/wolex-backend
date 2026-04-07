from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Profile, Settings
from .serializers import ProfileSerializer, ProfileUpdateSerializer, SettingsSerializer
from .utils import currency_for_nationality


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return Response(ProfileSerializer(profile).data)

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        ser = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        profile = ser.save()

        # if nationality provided and currency not manually set, try auto-populate
        nationality = request.data.get("nationality")
        if nationality:
            settings_obj, _ = Settings.objects.get_or_create(user=request.user)
            # only auto-set if current currency is empty or same as default
            auto_currency = currency_for_nationality(nationality)
            if auto_currency and (not settings_obj.currency or settings_obj.currency == ""):
                settings_obj.currency = auto_currency
                settings_obj.save()

        # assemble combined response for frontend
        user_data = {
            "id": request.user.id,
            "email": request.user.email,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "profile_completed": profile.is_complete,
            "email_verified": request.user.email_verified,
        }
        settings_obj, _ = Settings.objects.get_or_create(user=request.user)
        return Response({
            "message": "Profile updated successfully",
            "user": user_data,
            "profile": ProfileSerializer(profile).data,
            "settings": SettingsSerializer(settings_obj).data,
        })


class SettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings_obj, _ = Settings.objects.get_or_create(user=request.user)
        return Response(SettingsSerializer(settings_obj).data)

    def patch(self, request):
        settings_obj, _ = Settings.objects.get_or_create(user=request.user)
        ser = SettingsSerializer(settings_obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
