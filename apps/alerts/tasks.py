from django_q.tasks import schedule   # type: ignore[import]
from django_q.models import Schedule  # type: ignore[import]
from apps.alerts.services import check_balance_alert
from apps.users.models import User


def schedule_daily_balance_check():
    users = User.objects.all()
    for user in users:
        schedule(
            "apps.alerts.services.check_balance_alert",
            user.id,
            schedule_type=Schedule.DAILY,
        )