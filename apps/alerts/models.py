from django.db import models
from apps.users.models import User

# Create your models here.
class Alert(models.Model):
    ALERT_TYPES = [
        ("BUDGET", "Budget"),
        ("LARGE_TXN", "Large Transaction"),
        ("INFO", "Info"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.alert_type}"
    