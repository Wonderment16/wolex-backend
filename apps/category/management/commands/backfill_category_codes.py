from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.text import slugify

from apps.category.models import Category
from apps.transactions.models import Transaction


def _normalize(name: str) -> str:
    base = slugify(name, allow_unicode=False).replace("-", "_").upper()
    return base or "CATEGORY"


def _unique_code(base: str, cat_id: int) -> str:
    code = base[:40]
    if not Category.objects.filter(code=code).exclude(id=cat_id).exists():
        return code
    suffix = f"_{cat_id}"
    return f"{code[:40 - len(suffix)]}{suffix}"


class Command(BaseCommand):
    help = "Backfill missing category codes based on name"

    def handle(self, *args, **kwargs):
        updated = 0

        defaults = dict(Transaction.CATEGORY_CHOICES)
        for code, label in defaults.items():
            Category.objects.filter(
                user=None,
                name=label
            ).filter(
                Q(code__isnull=True) | Q(code="") | Q(code="TEMP")
            ).update(code=code)

        qs = Category.objects.filter(Q(code__isnull=True) | Q(code="") | Q(code="TEMP"))

        for cat in qs.iterator():
            base = _normalize(cat.name)
            cat.code = _unique_code(base, cat.id)
            cat.save(update_fields=["code"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} categories."))
