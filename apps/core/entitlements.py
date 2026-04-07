# apps/core/entitlements.py
from django.utils import timezone
from datetime import timedelta

TYPE_LIMITS = {
    "INDIVIDUAL": {
        "max_limit": 200,
        "history_days": 30,
        "max_push_items": 200,
        "can_sync": True,
        "can_push": True,
    },
    "FAMILY": {
        "max_limit": 500,
        "history_days": 365,
        "max_push_items": 500,
        "can_sync": True,
        "can_push": True,
    },
    "BUSINESS": {
        "max_limit": 500,
        "history_days": 3650,
        "max_push_items": 1000,
        "can_sync": True,
        "can_push": True,
    },
}

DEFAULT_TYPE = "INDIVIDUAL"

def _normalize_workspace_type(ws_type: str) -> str:
    if not ws_type:
        return DEFAULT_TYPE
    ws_type = str(ws_type).upper()
    if ws_type not in TYPE_LIMITS:
        return DEFAULT_TYPE
    return ws_type

def get_entitlements(user, workspace):
    ws_type = _normalize_workspace_type(getattr(workspace, "workspace_type", None))
    rules = TYPE_LIMITS[ws_type]

    return {
        "workspace_type": ws_type,
        "can_sync": rules["can_sync"],
        "can_push": rules["can_push"],
        "max_limit": rules["max_limit"],
        "history_days": rules["history_days"],
        "max_push_items": rules["max_push_items"],
        "server_time": timezone.now().isoformat(),
    }

def apply_history_window(qs, history_days: int):
    if not history_days:
        return qs
    cutoff = timezone.now() - timedelta(days=int(history_days))
    return qs.filter(updated_at__gt=cutoff)
