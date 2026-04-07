from django.db.models.functions import Lower
from rest_framework import serializers
from apps.users.plan import DEFAULT_WORKSPACE_TYPE, get_statement_bank_limit
from apps.workspaces.models import Membership, Workspace
from .models import BankStatement

class StatementUploadSerializer(serializers.ModelSerializer):
    workspace_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = BankStatement
        fields = [
            'id',
            'user',
            'file',
            'file_type',
            'analysis_result',
            'bank_name',
            'processed',
            'uploaded_at',
            'workspace_id',
        ]
        read_only_fields = ['id', 'user', 'analysis_result', 'processed', 'uploaded_at']

    def _resolve_workspace_type(self, user, workspace_id):
        if workspace_id is not None:
            ws = Workspace.objects.filter(id=workspace_id).first()
            if not ws:
                raise serializers.ValidationError({"workspace_id": "Workspace not found."})
            if not Membership.objects.filter(workspace=ws, user=user).exists():
                raise serializers.ValidationError({"workspace_id": "You don't belong to this workspace."})
            return ws.workspace_type

        ws = Workspace.objects.filter(created_by=user).order_by("created_at").first()
        if not ws:
            ws = Workspace.objects.filter(memberships__user=user).order_by("created_at").first()
        return ws.workspace_type if ws else DEFAULT_WORKSPACE_TYPE

    def validate(self, attrs):
        request = self.context.get("request")
        if not request or not getattr(request, "user", None):
            return attrs

        user = request.user
        bank_name = (attrs.get("bank_name") or "").strip()
        if not bank_name:
            return attrs

        workspace_id = attrs.get("workspace_id")
        workspace_type = self._resolve_workspace_type(user, workspace_id)
        limit = get_statement_bank_limit(user, workspace_type)

        existing_qs = (
            BankStatement.objects
            .filter(user=user)
            .exclude(bank_name__isnull=True)
            .exclude(bank_name__exact="")
        )
        if existing_qs.filter(bank_name__iexact=bank_name).exists():
            return attrs

        existing_count = (
            existing_qs
            .annotate(bank_name_l=Lower("bank_name"))
            .values("bank_name_l")
            .distinct()
            .count()
        )
        if existing_count >= limit:
            raise serializers.ValidationError(
                {"bank_name": f"Bank limit reached for your plan ({limit} max)."}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("workspace_id", None)
        return super().create(validated_data)

    def validate_file(self, file):
        allowed_types = ["application/pdf", "text/csv"]
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Unsupported file type")
        return file
