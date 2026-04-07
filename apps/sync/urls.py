from django.urls import path
from .views import SyncBootstrapView, SyncPullView, SyncPushView

urlpatterns = [
    path("bootstrap/", SyncBootstrapView.as_view()),
    path("pull/", SyncPullView.as_view()),
    path("push/", SyncPushView.as_view()),
]

