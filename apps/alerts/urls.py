from rest_framework.routers import DefaultRouter
from .views import AlertViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alerts')

urlpatterns = [
    path('', include(router.urls)),
]
