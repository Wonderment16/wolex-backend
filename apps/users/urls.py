from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .views import auth_home
from apps.users.api.views import (
    CustomTokenObtainPairView,
    RegisterView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerificationRequestView,
    EmailVerificationConfirmView,
    GoogleAuthView,
)

urlpatterns = [
    path('', auth_home, name='auth-home'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('verify-email/request/', EmailVerificationRequestView.as_view(), name='email_verify_request'),
    path('verify-email/confirm/', EmailVerificationConfirmView.as_view(), name='email_verify_confirm'),
    path('google/', GoogleAuthView.as_view(), name='google_auth'),
    path('', include('rest_framework.urls')),
]
