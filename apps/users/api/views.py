from django.shortcuts import render
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from apps.users.models import Balance

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView

from apps.transactions.models import Transaction

from .serializers import (
    UserContextSerializer,
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
)
from drf_spectacular.utils import extend_schema

from django.db.models import Sum

User = get_user_model()


# Create your views here.
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@method_decorator(csrf_exempt, name='dispatch') # Add this line
class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        print(f"DEBUG: Received registration data: {request.data.get('email')}")
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # generate tokens
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        tokens = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
        # after creating user send verification email
        token2 = PasswordResetTokenGenerator().make_token(user)
        uid2 = urlsafe_base64_encode(force_bytes(user.pk))
        verify_link = f"{settings.FRONTEND_URL}/verify-email?uid={uid2}&token={token2}"
        send_mail(
            subject='Verify your Wolex email',
            message=f'Click to verify your email: {verify_link}',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@wolex.com'),
            recipient_list=[user.email],
        )

        response_data = {
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_completed': getattr(user, 'profile_completed', False),
                'email_verified': user.email_verified,
            },
            'tokens': tokens,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    # throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        email = request.data.get('email')
        print("PASSWORD RESET REQUEST:", request.data)
        if not email:
            return Response(
                {"error": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"error": "Invalid email address."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        if user:
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            from urllib.parse import urlencode

            params = urlencode({
                "uid": uid,
                "token": token
            })

            reset_link = f"{settings.FRONTEND_URL}/pages/reset_password.html?{params}"
            # send email; actual email backend must be configured
            # send_mail(
            #     subject="Wolex password reset",
            #     from_email="noreply@wolex.com",
            #     recipient_list=[user.email],
            #     message = f"""
            #     Click the link below to reset your password:\n\n{reset_link}
            #     """
            # )

            from django.core.mail import EmailMultiAlternatives

            email = EmailMultiAlternatives(
                subject="Wolex password reset",
                body=f"Reset your password using the link below:\n{reset_link}",
                from_email="noreply@wolex.com",
                to=[user.email],
            )

            html_content = f"""
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                """

            email.attach_alternative(html_content, "text/html")

            email.send()
                        
        return Response({'message': 'If an account with that email exists, instructions have been sent.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print("PASSWORD RESET CONFIRM:", request.data)

        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not uid or not token or not new_password:
            return Response({"error": "Missing credentials."}, status=400)


        # If the email system turned "=" into "3D", fix it here
        if uid and uid.startswith('3D'):
            uid = uid.replace('3D', '', 1)

        if uid.startswith('3D'):
            uid = uid[2:]
        if token.startswith('3D'):
            token = token[2:]

        try:
            # 1. Decode the base64 to bytes
            uid_bytes = urlsafe_base64_decode(uid)
            # 2. Convert bytes to string (the ID)
            uid = force_str(uid_bytes)
            # 3. Get the user
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist, Exception) as e:
            print(f"DECODE ERROR: {e}")
            return Response({"error": "Invalid link."}, status=400)
        print("UID:", uid)
        print("TOKEN:", token)

        print("TOKEN VALID:", PasswordResetTokenGenerator().check_token(user, token))

        # Check token
        if not PasswordResetTokenGenerator().check_token(user, token):
            print(f"UID: {uid} | TOKEN: {token}")
            return Response({'error': 'Invalid or expired token.'}, status=400)
            
        # Validate and save
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password, user)
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password has been reset.'})
        except Exception as exc:
            return Response({'errors': exc.messages}, status=400)




class EmailVerificationRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'email_verification'

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None
            if user and not user.email_verified:
                token = PasswordResetTokenGenerator().make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                verify_link = f"{getattr(settings, 'FRONTEND_URL', '')}/verify-email?uid={uid}&token={token}"
                send_mail(
                    subject='Verify your Wolex email',
                    message=f'Click to verify your email: {verify_link}',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@wolex.com'),
                    recipient_list=[user.email],
                )

        return Response({'message': 'If an account with that email exists, verification instructions have been sent.'})

        

class EmailVerificationConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'error': 'Invalid link.'}, status=status.HTTP_400_BAD_REQUEST)
        if PasswordResetTokenGenerator().check_token(user, token):
            user.email_verified = True
            user.save()
            return Response({'message': 'Email verified.'})
        return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'google_auth'

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        # verify with google
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
        except ImportError:
            return Response({'error': 'Google auth library not installed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if not settings.GOOGLE_CLIENT_ID:
            return Response(
        {'error': 'Google auth is not configured.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
        try:
            idinfo = google_id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
        except Exception:
            return Response(
                {'error': 'Invalid Google token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = idinfo.get('email')
        google_email_verified = idinfo.get('email_verified', False)
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')

        if not email:
            return Response(
                {'error': 'Google token did not contain email.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not google_email_verified:
            return Response(
                {'error': 'Google email is not verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email_verified': True,
            }
        )

        if not created:
            updated = False
            if not user.first_name and first_name:
                user.first_name = first_name
                updated = True
            if not user.last_name and last_name:
                user.last_name = last_name
                updated = True
            if not user.email_verified:
                user.email_verified = True
                updated = True
            if updated:
                user.save()

        from apps.profiles.models import Profile, Settings
        Profile.objects.get_or_create(user=user)
        Settings.objects.get_or_create(user=user)
        # obtain tokens
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        access = str(refresh.access_token)
        refresh_token = str(refresh)
        profile_completed = getattr(user, 'profile_completed', False)
        return Response({
            'message': 'Google authentication successful',
            'is_new_user': created,
            'access': access,
            'refresh': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_completed': profile_completed,
            }
        })


@extend_schema(
    summary="Get User Context",
    description="Retrieve the authenticated user's context information.",
)


class UserContextView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chatbot'


    def get(self, request):
        Balance.objects.get_or_create(user=request.user, defaults={"amount": 0.00})
        # 1. Initialize the serializer with the user
        serializer = UserContextSerializer(request.user)
        
        # 2. Get the serialized data (this handles the balance, transactions, etc.)
        data = serializer.data
        
        # 3. Add the extra fields you wanted to include
        data.update({
            "id": request.user.id,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
        })
        
        # 4. Return the single data object
        return Response(data, status=status.HTTP_200_OK)
