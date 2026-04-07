from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet
from .views import list_categories
from django.urls import path

router = DefaultRouter()
router.register(r"", CategoryViewSet, basename="category")


urlpatterns = [
    *router.urls,
    path("categories/", list_categories)
]