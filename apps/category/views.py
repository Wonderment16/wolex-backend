from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from apps.category.models import Category
from .serializers import CategorySerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def list_categories(request):
    categories = Category.objects.all().values("id", "name", "code", "kind")
    return Response(categories)


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # show default categories + user's custom ones
        return Category.objects.filter(user__isnull=True) | Category.objects.filter(user=user)

    def perform_create(self, serializer):
        # user-created categories belong to user
        serializer.save(user=self.request.user, is_default=False)
