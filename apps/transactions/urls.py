from rest_framework import routers
from apps.transactions.views import (
    TransactionViewSet,
    TransactionSummaryView,
    MonthlySummaryView,
    WeeklySummaryView,
    CategorySummaryView,
    DashboardView,
)
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('summary/', TransactionSummaryView.as_view(), name='transaction-summary'),
    path('analysis/monthly/', MonthlySummaryView.as_view(), name='monthly-summary'),
    path('analysis/weekly/', WeeklySummaryView.as_view(), name='weekly-summary'),
    path('analysis/category/', CategorySummaryView.as_view(), name='category-summary'),
]
