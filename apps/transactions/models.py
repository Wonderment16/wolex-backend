from django.db import models
from django.conf import settings

from apps.users.models import User

# Create your models here.

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('EARNED', 'Earned'),
        ('PURCHASED', 'Purchased'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"
    

    CATEGORY_CHOICES = [
        ("FOOD", "Food"),
        ("TRANSPORTATION", "Transportation"),
        ("ACADEMIC", "Academic"),
        ("BILLS AND UTILITIES", "Bills andUtilities"),
        ("SUBSCRIPTIONS", "Subscriptions"),
        ("HEALTH AND FITNESS", "Health and Fitness"),
        ("MISCELLANEOUS", "Miscellaneous"),
    ]

    category = models.CharField(max_length = 40, choices=CATEGORY_CHOICES, default="MISCELLANEOUS")

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.CharField(max_length=40, choices=Transaction.CATEGORY_CHOICES)
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.user.email} - {self.category} - {self.limit_amount}"