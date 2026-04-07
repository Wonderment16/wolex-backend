from django.db import models
from django.conf import settings


class Workspace(models.Model):
    TYPES = (
        ("INDIVIDUAL", "Individual"),
        ("FAMILY", "Family"),
        ("BUSINESS", "Business"),
    )

    name = models.CharField(max_length=80)
    workspace_type = models.CharField(max_length=20, choices=TYPES, default="INDIVIDUAL")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_workspaces"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.workspace_type})"


class Membership(models.Model):
    ROLES = (
        ("OWNER", "Owner"),
        ("ADMIN", "Admin"),
        ("MEMBER", "Member"),
    )

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=ROLES, default="MEMBER")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("workspace", "user")

    def __str__(self):
        return f"{self.user} in {self.workspace} as {self.role}"
