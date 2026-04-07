from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import WorkspaceViewSet, WorkspaceMembersView, WorkspaceMembersListView, WorkspaceMemberRemoveView, WorkspaceMemberAddView

router = DefaultRouter()
router.register(r"", WorkspaceViewSet, basename="workspace")

# Combine all additional workspace-related routes in a single urlpatterns list.
urlpatterns = router.urls + [
    path("<int:workspace_id>/members/", WorkspaceMembersListView.as_view()),
    path("<int:workspace_id>/members/add/", WorkspaceMemberAddView.as_view()),
    path("<int:workspace_id>/members/remove/", WorkspaceMemberRemoveView.as_view()),
]

