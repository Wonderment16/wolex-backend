from django.core.management.base import BaseCommand
from apps.category.models import Category


class Command(BaseCommand):
    help = "Seed default Wolex categories"

    def handle(self, *args, **kwargs):
        defaults = [
            ("FOOD", "Food", "EXPENSE"),
            ("TRANSPORTATION", "Transportation", "EXPENSE"),
            ("ACADEMIC", "Academic", "EXPENSE"),
            ("BILLS_AND_UTILITIES", "Bills and Utilities", "EXPENSE"),
            ("SUBSCRIPTIONS", "Subscriptions", "EXPENSE"),
            ("HEALTH_AND_FITNESS", "Health and Fitness", "EXPENSE"),
            ("MISCELLANEOUS", "Miscellaneous", "EXPENSE"),
            ("SALARY", "Salary", "INCOME"),
        ]

        created = 0
        for code, name, kind in defaults:
            obj, was_created = Category.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "kind": kind,
                    "is_default": True,
                    "user": None,
                }
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded categories. Created: {created}"))
