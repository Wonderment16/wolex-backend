from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Workspace, Membership
from .serializers import WorkspaceSerializer

from rest_framework.exceptions import PermissionDenied
from apps.users.plan import get_sync_limits

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.users.limits import get_limits

from apps.users.models import User



class WorkspaceViewSet(ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Workspace.objects.filter(memberships__user=user).distinct()

    
    def perform_create(self, serializer):
        user = self.request.user
        workspace_type = serializer.validated_data.get("workspace_type", "INDIVIDUAL")

        limits = get_limits(user, workspace_type)

        # how many workspaces this user is already a member of
        current_count = Membership.objects.filter(user=user).count()
        if current_count >= limits["max_workspaces"]:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"error": "Workspace limit reached for your plan."})

        ws = serializer.save(created_by=user)
        Membership.objects.create(workspace=ws, user=user, role="OWNER")




class WorkspaceMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, workspace_id: int):
        """
        Add a member to workspace

        Payload:
        {
        "user_email": "someone@gmail.com",
        "role": "MEMBER"   # optional: OWNER | ADMIN | MEMBER
        }
        """

        # 1) workspace exists?
        ws = Workspace.objects.filter(id=workspace_id).first()
        if not ws:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        # 2) requester must be in workspace
        requester_membership = Membership.objects.filter(workspace=ws, user=request.user).first()
        if not requester_membership:
            return Response({"error": "You don't belong to this workspace"}, status=status.HTTP_403_FORBIDDEN)

        # 3) only OWNER/ADMIN can add people
        if requester_membership.role not in ["OWNER", "ADMIN"]:
            raise PermissionDenied("You don't have permission to add members.")

        # 4) enforce plan limits (max_members depends on plan + workspace_type)
        limits = get_sync_limits(request.user, ws)
        member_count = Membership.objects.filter(workspace=ws).count()

        if member_count >= limits["max_members"]:
            raise PermissionDenied(f"Member limit reached. Max is {limits['max_members']}.")

        # 5) get user to add
        user_email = request.data.get("user_email")
        if not user_email:
            return Response({"error": "user_email is required"}, status=status.HTTP_400_BAD_REQUEST)

        user_to_add = User.objects.filter(email=user_email).first()
        if not user_to_add:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # 6) prevent duplicate membership
        if Membership.objects.filter(workspace=ws, user=user_to_add).exists():
            return Response({"error": "User is already a member"}, status=status.HTTP_400_BAD_REQUEST)

        # 7) role
        role = request.data.get("role", "MEMBER")
        if role not in ["OWNER", "ADMIN", "MEMBER"]:
            return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

        # Don't let ADMIN create another OWNER (optional rule)
        if role == "OWNER" and requester_membership.role != "OWNER":
            raise PermissionDenied("Only OWNER can assign OWNER role.")

        mem = Membership.objects.create(workspace=ws, user=user_to_add, role=role)

        return Response({
            "message": "Member added",
            "workspace_id": ws.id,
            "user_email": user_to_add.email,
            "role": mem.role
        }, status=status.HTTP_201_CREATED)

class WorkspaceMembersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id: int):
        ws = Workspace.objects.filter(id=workspace_id).first()
        if not ws:
            return Response({"error": "Workspace not found"}, status=404)

        if not Membership.objects.filter(workspace=ws, user=request.user).exists():
            return Response({"error": "You don't belong to this workspace"}, status=403)

        members = Membership.objects.filter(workspace=ws).select_related("user")
        data = [
            {
                "user_id": m.user_id,
                "email": m.user.email,
                "role": m.role,
                "joined_at": m.joined_at,
            }
            for m in members
        ]
        return Response({"workspace_id": ws.id, "members": data})

class WorkspaceMemberRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, workspace_id: int):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        ws = Workspace.objects.filter(id=workspace_id).first()
        if not ws:
            return Response({"error": "Workspace not found"}, status=404)

        requester = Membership.objects.filter(workspace=ws, user=request.user).first()
        if not requester:
            return Response({"error": "You don't belong to this workspace"}, status=403)

        if requester.role not in ["OWNER", "ADMIN"]:
            return Response({"error": "No permission"}, status=403)

        target = Membership.objects.filter(workspace=ws, user_id=user_id).first()
        if not target:
            return Response({"error": "Member not found"}, status=404)

        # block removing OWNER unless requester is OWNER
        if target.role == "OWNER" and requester.role != "OWNER":
            return Response({"error": "Only OWNER can remove OWNER"}, status=403)

        target.delete()
        return Response({"message": "Member removed"})


class WorkspaceMemberAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, workspace_id: int):
        from apps.users.limits import get_limits

        user_id = request.data.get("user_id")
        role = request.data.get("role", "MEMBER")

        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        ws = Workspace.objects.filter(id=workspace_id).first()
        if not ws:
            return Response({"error": "Workspace not found"}, status=404)

        requester = Membership.objects.filter(workspace=ws, user=request.user).first()
        if not requester:
            return Response({"error": "You don't belong to this workspace"}, status=403)

        if requester.role not in ["OWNER", "ADMIN"]:
            return Response({"error": "No permission"}, status=403)

        limits = get_limits(request.user, ws.workspace_type)
        members_count = Membership.objects.filter(workspace=ws).count()

        if members_count >= limits["max_members"]:
            return Response({"error": "Member limit reached for this plan."}, status=403)

        Membership.objects.get_or_create(
            workspace=ws,
            user_id=user_id,
            defaults={"role": role}
        )
        return Response({"message": "Member added"})
