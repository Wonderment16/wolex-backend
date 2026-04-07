SYNC_LIMITS = {
    ("FREE", "INDIVIDUAL"): {"pull_limit": 100, "push_max_items": 100, "max_workspaces": 1, "max_members": 1},
    ("FREE", "FAMILY"):     {"pull_limit": 150, "push_max_items": 150, "max_workspaces": 1, "max_members": 5},
    ("FREE", "BUSINESS"):   {"pull_limit": 200, "push_max_items": 200, "max_workspaces": 1, "max_members": 10},

    ("PLUS", "INDIVIDUAL"): {"pull_limit": 300, "push_max_items": 300, "max_workspaces": 3, "max_members": 1},
    ("PLUS", "FAMILY"):     {"pull_limit": 400, "push_max_items": 400, "max_workspaces": 3, "max_members": 8},
    ("PLUS", "BUSINESS"):   {"pull_limit": 500, "push_max_items": 500, "max_workspaces": 5, "max_members": 25},

    ("PRO", "INDIVIDUAL"):  {"pull_limit": 500, "push_max_items": 500, "max_workspaces": 10, "max_members": 1},
    ("PRO", "FAMILY"):      {"pull_limit": 700, "push_max_items": 700, "max_workspaces": 10, "max_members": 15},
    ("PRO", "BUSINESS"):    {"pull_limit": 1000, "push_max_items": 1000, "max_workspaces": 30, "max_members": 100},
}

# Max number of distinct currencies allowed per workspace, by plan/workspace type.
# None means unlimited currencies.
CURRENCY_LIMITS = {
    ("FREE", "INDIVIDUAL"): 1,
    ("FREE", "FAMILY"): 1,
    ("FREE", "BUSINESS"): 1,

    ("PLUS", "INDIVIDUAL"): None,
    ("PLUS", "FAMILY"): None,
    ("PLUS", "BUSINESS"): None,

    ("PRO", "INDIVIDUAL"): None,
    ("PRO", "FAMILY"): None,
    ("PRO", "BUSINESS"): None,
}

# Prices in NGN for paid accounts by workspace type.
PRICING_NGN = {
    "INDIVIDUAL": 5000,
    "BUSINESS": 8000,
    "FAMILY": 120000,
}

# Max number of distinct banks a user can upload statements for, by plan/workspace type.
STATEMENT_BANK_LIMITS = {
    ("FREE", "INDIVIDUAL"): 1,
    ("FREE", "FAMILY"): 3,
    ("FREE", "BUSINESS"): 3,

    ("PLUS", "INDIVIDUAL"): 3,
    ("PLUS", "FAMILY"): 7,
    ("PLUS", "BUSINESS"): 5,

    ("PRO", "INDIVIDUAL"): 3,
    ("PRO", "FAMILY"): 7,
    ("PRO", "BUSINESS"): 5,
}

DEFAULT_PLAN = "FREE"
DEFAULT_WORKSPACE_TYPE = "INDIVIDUAL"


def _get_plan_for_user(user) -> str:
    # Safest fallback so the backend doesn't crash if plan data is missing.
    plan = getattr(user, "plan", None)
    if not plan and hasattr(user, "profile"):
        plan = getattr(user.profile, "plan", None)
    return (plan or DEFAULT_PLAN).upper()


def get_pricing_ngn(workspace_type: str) -> int:
    ws_type = (workspace_type or DEFAULT_WORKSPACE_TYPE).upper()
    return PRICING_NGN.get(ws_type, PRICING_NGN[DEFAULT_WORKSPACE_TYPE])


def get_sync_limits(user, workspace) -> dict:
    plan = _get_plan_for_user(user)
    ws_type = (getattr(workspace, "workspace_type", None) or DEFAULT_WORKSPACE_TYPE).upper()

    key = (plan, ws_type)
    if key not in SYNC_LIMITS:
        key = (DEFAULT_PLAN, DEFAULT_WORKSPACE_TYPE)

    return SYNC_LIMITS[key]


def get_statement_bank_limit(user, workspace_type: str) -> int:
    plan = _get_plan_for_user(user)
    ws_type = (workspace_type or DEFAULT_WORKSPACE_TYPE).upper()

    key = (plan, ws_type)
    if key not in STATEMENT_BANK_LIMITS:
        key = (DEFAULT_PLAN, DEFAULT_WORKSPACE_TYPE)

    return STATEMENT_BANK_LIMITS[key]


def get_currency_limit(user, workspace_type: str):
    plan = _get_plan_for_user(user)
    ws_type = (workspace_type or DEFAULT_WORKSPACE_TYPE).upper()

    key = (plan, ws_type)
    if key not in CURRENCY_LIMITS:
        key = (DEFAULT_PLAN, DEFAULT_WORKSPACE_TYPE)

    return CURRENCY_LIMITS[key]
