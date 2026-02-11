from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

from .serializers import UserContextSerializer
from drf_spectacular.utils import extend_schema


# Create your views here.
@extend_schema(
    summary="Get User Context",
    description="Retrieve the authenticated user's context information.",
)


class UserContextView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chatbot'

    def get(self, request):
        serializer = UserContextSerializer(request.user)
        return Response(serializer.data)
    

