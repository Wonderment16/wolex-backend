from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    name = 'apps.transactions'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        # Import signals to ensure signal handlers are registered
        from . import signals


