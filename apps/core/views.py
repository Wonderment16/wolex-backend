from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

def home(request):
    return HttpResponse("Welcome to the Wolex Application!")

class HealthCheckView(APIView):
    authentication_classes = []

    def get(self, request):
        return Response({
            "status": "ok",
            "service": "wolex_backend"
        })