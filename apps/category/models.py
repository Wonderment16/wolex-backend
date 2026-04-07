from django.db import models
from django.conf import settings

# Create your models here.
class Category(models.Model):
    CATEGORY_KINDS = (
        ("EXPENSE", "Expense"),
        ("INCOME", "Income"),
    )

    name = models.CharField(max_length=60)
    kind = models.CharField(max_length=10, choices=CATEGORY_KINDS, default="EXPENSE")
    code = models.CharField(max_length=40, unique=True)


    # if user is null => default category for everyone
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="categories"
    )

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "name")  # user can't have duplicate names

    def __str__(self):
        return f"{self.name} ({'default' if self.is_default else 'custom'})"
