from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.views import TokenObtainPairView

@method_decorator(csrf_exempt, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    # You can customize the serializer if needed
    pass


def auth_home(request):
    return redirect('rest_framework:login')


def profile_home(request):
    # Simple placeholder profile page so /accounts/profile/ resolves.
    return HttpResponse(
        "<h1>Profile</h1><p>You are logged in.</p>"
    )
