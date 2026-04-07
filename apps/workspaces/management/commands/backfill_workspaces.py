from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace, Membership
from apps.transactions.models import Transaction


class Command(BaseCommand):
    help = "Create a Personal workspace per user and assign their transactions."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        created_ws = 0
        updated_tx = 0

        for user in User.objects.all().iterator():
            ws, created = Workspace.objects.get_or_create(
                created_by=user,
                name="Personal",
                defaults={"workspace_type": "INDIVIDUAL"}
            )
            if created:
                created_ws += 1

            Membership.objects.get_or_create(
                workspace=ws,
                user=user,
                defaults={"role": "OWNER"}
            )

            # assign existing txns
            count = Transaction.objects.filter(user=user, workspace__isnull=True).update(workspace=ws)
            updated_tx += count

        self.stdout.write(self.style.SUCCESS(
            f"Created workspaces: {created_ws}, Updated transactions: {updated_tx}"
        ))
