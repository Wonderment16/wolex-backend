from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.transactions.models import Transaction
from apps.alerts.models import Alert

@receiver(post_save, sender=Transaction)
def create_transaction_alert(sender, instance, created, **kwargs):
    if created:
        Alert.objects.create(
            user=instance.user,
            message=f"{instance.amount} added as {instance.transaction_type.lower()}",
        )

            

@receiver(post_save, sender=Transaction)
def update_user_balance(sender, instance, created, **kwargs):
    if not created:
        return

    from apps.users.models import Balance

    balance, _ = Balance.objects.get_or_create(user=instance.user)

    if instance.transaction_type == "INCOME":
        balance.amount += instance.amount
    elif instance.transaction_type == "EXPENSE":
        balance.amount -= instance.amount

    balance.save()     
