from django.db import models

from apps.users.models import User

# Create your models here.
class Insight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    insight_type = models.CharField(max_length=50)
    message = models.TestField()
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=1)