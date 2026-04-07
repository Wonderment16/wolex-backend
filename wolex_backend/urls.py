"""
URL configuration for wolex_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.core.views import home
from apps.users.views import profile_home
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import HealthCheckView, index, PricingView
from rest_framework.routers import DefaultRouter
from apps.transactions.views import DashboardView, TransactionViewSet

router = DefaultRouter()
router.register(r"transactions", TransactionViewSet, basename="transactions")


from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/alerts', include('apps.alerts.urls')),
    path("api/", include(router.urls)),
    path("api/dashboard/", DashboardView.as_view()),
    path("", home),
    path('accounts/profile/', profile_home, name='account-profile'),
    path('api/statements/', include('apps.statements.urls')),
    path('api/users/', include('apps.users.api.urls')),
    path('api/chatbot/', include('apps.chatbot.urls')),
    path('api/pricing/', PricingView.as_view(), name='pricing'),
    path("healthz/", HealthCheckView.as_view()),
    path("api/profiles/", include('apps.profiles.urls')),
    path("api/category/", include("apps.category.urls")),
    path("api/workspaces/", include("apps.workspaces.urls")),
    path("api/sync/", include("apps.sync.urls")),
    path("chatbot/", include("apps.chatbot.urls")),
]

urlpatterns += static(
    settings.MEDIA_URL, 
    document_root=settings.MEDIA_ROOT
    )

# API schema and documentation
urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'))
    ]
