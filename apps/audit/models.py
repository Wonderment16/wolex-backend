from django.db import models
from apps.users.models import User

# Create your models here.
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    metadata = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)