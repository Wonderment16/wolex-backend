import re

from apps.users.plan import get_currency_limit
from apps.workspaces.models import Workspace
from apps.transactions.models import Transaction


CURRENCY_CODE_RE = re.compile(r"^[A-Z]{3}$")


class CurrencyValidationError(ValueError):
    pass


def normalize_currency(value):
    if value is None:
        return None
    return str(value).strip().upper()


def get_user_currency(user) -> str:
    if not user:
        return "NGN"
    settings = getattr(user, "settings", None)
    currency = getattr(settings, "currency", None)
    return normalize_currency(currency) or "NGN"


def validate_currency_code(value: str) -> str:
    normalized = normalize_currency(value)
    if not normalized or not CURRENCY_CODE_RE.match(normalized):
        raise CurrencyValidationError("Currency must be a 3-letter ISO code (e.g., USD, NGN).")
    return normalized


def resolve_workspace(user, workspace_id=None):
    if workspace_id:
        try:
            workspace_id = int(workspace_id)
        except (TypeError, ValueError):
            workspace_id = None
    if workspace_id:
        return Workspace.objects.filter(id=workspace_id).first()
    return Workspace.objects.filter(created_by=user, name="Personal").first()


def enforce_currency_limit(user, workspace, currency, instance=None):
    if not user or not workspace:
        return
    limit = get_currency_limit(user, workspace.workspace_type)
    if not limit:
        return

    qs = Transaction.objects.filter(user=user, workspace=workspace).values_list("currency", flat=True).distinct()
    if instance and getattr(instance, "pk", None):
        qs = qs.exclude(pk=instance.pk)

    existing = {c for c in qs if c}
    if not existing:
        return
    if currency in existing:
        return
    if len(existing) >= limit:
        raise CurrencyValidationError("Your plan allows only 1 currency per workspace.")
