from apps.users.plan import SYNC_LIMITS

def get_user_plan(user) -> str:
    """
    Return plan name like FREE / PLUS / PRO.
    Adapt this line to your user model field.
    """
    return getattr(user, "plan", "FREE")  # or user.account_plan, user.subscription_plan etc.

def get_limits(user, workspace_type: str) -> dict:
    plan = get_user_plan(user)
    return SYNC_LIMITS.get((plan, workspace_type), SYNC_LIMITS[("FREE", "INDIVIDUAL")])
