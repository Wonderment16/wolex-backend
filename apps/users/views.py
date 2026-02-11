from django.shortcuts import redirect
from django.http import HttpResponse


def auth_home(request):
    return redirect('rest_framework:login')


def profile_home(request):
    # Simple placeholder profile page so /accounts/profile/ resolves.
    return HttpResponse(
        "<h1>Profile</h1><p>You are logged in.</p>"
    )
