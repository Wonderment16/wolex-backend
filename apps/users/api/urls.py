from django.urls import path
from .views import UserContextView


urlpatterns = [
    path('context/', UserContextView.as_view(), name='user-context'),
]