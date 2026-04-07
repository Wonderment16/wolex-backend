from django.db import migrations


def forwards(apps, schema_editor):
    Transaction = apps.get_model("transactions", "Transaction")
    Transaction.objects.filter(transaction_type="EARNED").update(transaction_type="INCOME")
    Transaction.objects.filter(transaction_type="PURCHASED").update(transaction_type="EXPENSE")


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0008_transaction_currency"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
