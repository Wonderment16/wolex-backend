from django.db import models
from apps.users.models import User


class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('TRANSACTION', 'Transaction'),
        ('STATEMENT', 'Statement'),
        ('PROFILE', 'Profile'),
        ('SYSTEM', 'System'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    message = models.CharField(max_length=255)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.activity_type}"
