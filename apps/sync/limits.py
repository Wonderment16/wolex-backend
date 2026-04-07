# apps/sync/limits.py

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

DEFAULT_PLAN = "FREE"
DEFAULT_WORKSPACE_TYPE = "INDIVIDUAL"


def get_plan_for_user(user) -> str:
    """
    Replace this with your real source of plan.
    Common options:
    - user.profile.plan
    - user.plan
    - user.subscription.plan
    """
    # safest fallback so your backend never crashes:
    plan = getattr(user, "plan", None)
    if not plan and hasattr(user, "profile"):
        plan = getattr(user.profile, "plan", None)
    return (plan or DEFAULT_PLAN).upper()


def get_limits(user, workspace) -> dict:
    plan = get_plan_for_user(user)
    ws_type = (getattr(workspace, "workspace_type", None) or DEFAULT_WORKSPACE_TYPE).upper()

    # fallback if weird values sneak in
    key = (plan, ws_type)
    if key not in SYNC_LIMITS:
        key = (DEFAULT_PLAN, DEFAULT_WORKSPACE_TYPE)

    return SYNC_LIMITS[key]
