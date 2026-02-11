from apps.activity.models import Activity


def log_activity(user, activity_type, message, metadata=None):
    Activity.objects.create(
        user=user,
        activity_type=activity_type,
        message=message,
        metadata=metadata or {}
    )
