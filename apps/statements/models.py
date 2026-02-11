from django.db import models
from apps.users.models import User

# Create your models here.
class BankStatement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="statements")

    file = models.FileField(upload_to='statements/')
    file_type = models.CharField(
        max_length=20,
        choices=[
            ('PDF', 'PDF'),
            ('CSV', 'CSV'),
            ('XLSX', 'Excel'),
        ]
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    bank_name = models.CharField(max_length=100, blank=True)

    # Analyze
    processed = models.BooleanField(default=False)
    analysis_result = models.JSONField(blank=True, null=True)
    version = models.PositiveIntegerField(default=1)


    def __str__(self):
        return f"{self.user.email} - Statement {self.file.name} ({self.bank_name})"