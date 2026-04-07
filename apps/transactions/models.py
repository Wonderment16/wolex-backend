from django.db import models
from django.conf import settings

from apps.workspaces.models import Workspace
from apps.category.models import Category
from apps.users.models import User

# Create your models here.

import uuid
from django.utils import timezone


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transactions",
    )

    

    CATEGORY_CHOICES = [
        ("FOOD", "Food"),
        ("SALARY", "Salary"),
        ("TRANSPORTATION", "Transportation"),
        ("GIFT", "Gift"),
        ("ACADEMICS", "Academics"),
        ("SHOPPING", "Shopping"),
        ("BILLS AND UTILITIES", "Bills and Utilities"),
        ("SUBSCRIPTIONS", "Subscriptions"),
        ("HEALTH AND FITNESS", "Health and Fitness"),
        ("MISCELLANEOUS", "Miscellaneous"),
    ]

    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="NGN")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    client_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    category_fk = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transactions"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "client_id"],
                name="uniq_txn_per_workspace_client",
            )
        ]
        indexes = [
            models.Index(fields=["workspace", "updated_at", "id"]),
        ]




    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"



class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2)

    category_fk = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="budgets"
    )
    def __str__(self):
        return f"{self.user.email} - {self.category} - {self.limit_amount}"
