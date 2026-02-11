from apps.users.models import Balance, User
from apps.alerts.models import Alert
from django.core.mail import send_mail

def check_balance_alert(user_or_id, threshold=100):
    """Check a user's balance and create a budget alert if below threshold.

    Accepts either a User instance or a user id (int) so this can be used
    directly with django-q scheduled tasks which pass primitive args.
    """
    if isinstance(user_or_id, int):
        try:
            user = User.objects.get(pk=user_or_id)
        except User.DoesNotExist:
            return
    else:
        user = user_or_id

    # Prefer the Balance one-to-one instance when available, fallback to calculated value
    balance_obj = getattr(user, 'balance', None)
    if balance_obj is not None:
        balance_value = balance_obj.amount
    else:
        balance_value = getattr(user, 'calculated_balance', 0)

    if balance_value < threshold:
        Alert.objects.create(
            user=user,
            alert_type="BUDGET",
            message=f"Your balance is low. Consider adding funds or reviewing spending."
        )
        
    # Send mail
    send_mail(
        subject="Wolex Alert: Low Balance",
        message=f"Dear {user.first_name},\n\nYour current balance is low.\n\nBest regards,\nWolex Team",
        from_email="noreply@wolex.com",
        recipient_list=[user.email],
    )