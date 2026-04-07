from django.core.management.base import BaseCommand
from apps.transactions.models import Transaction
from apps.category.models import Category

class Command(BaseCommand):
    help = "Backfill Transaction.category_obj from Transaction.category (choices)."

    def handle(self, *args, **options):
        # Make default categories from your choices
        defaults = dict(Transaction.CATEGORY_CHOICES)

        created = 0
        updated = 0

        for code, label in defaults.items():
            obj, was_created = Category.objects.get_or_create(
                user=None,
                name=label,
                defaults={"is_default": True, "kind": "EXPENSE"}
            )
            if was_created:
                created += 1

        # Map code -> Category
        code_to_cat = {}
        for code, label in defaults.items():
            code_to_cat[code] = Category.objects.get(user=None, name=label)

        qs = Transaction.objects.filter(category_obj__isnull=True)

        for txn in qs.iterator():
            cat = code_to_cat.get(txn.category)
            if cat:
                txn.category_obj = cat
                txn.save(update_fields=["category_obj"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Created defaults: {created}, Updated transactions: {updated}"
        ))
