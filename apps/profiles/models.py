from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.users.models import User

class Profile(models.Model):
    ACCOUNT_TYPES = [
        ("INDIVIDUAL", "Individual"),
        ("BUSINESS", "Business"),
        ("FAMILY", "Family"),
    ]

    COUNTRY_CHOICES = [
        ("Nigeria", "Nigeria"),
        ("South Africa", "South Africa"),
        ("United States", "United States"),
        ("Mexico", "Mexico"),
        ("United Kingdom", "United Kingdom"),
        ("Canada", "Canada"),
        ("India", "India"),
        ("Italy", "Italy"),
        ("China", "China"),
        ("Germany", "Germany"),
        ("France", "France"),
        ("Japan", "Japan"),
        ("Ghana", "Ghana"),
        ("Egypt", "Egypt"),
        ("Brazil", "Brazil"),
        ("Australia", "Australia"),
        ("Argentina", "Argentina"),
        ("Peru", "Peru"),
        ("New Zealand", "New Zealand"),
        ("Nepal", "Nepal")
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    middle_name = models.CharField(max_length=30, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    profession = models.CharField(max_length=100, blank=True, default="")
    nationality = models.CharField(max_length=100, blank=True, choices=COUNTRY_CHOICES)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default="INDIVIDUAL")

    # flag to indicate whether onboarding/profile completion has happened
    is_complete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return getattr(self.user, "email", str(self.user))


class Settings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settings"
    )
    currency = models.CharField(max_length=10, default="NGN")
    notifications_enabled = models.BooleanField(default=True)
    theme = models.CharField(max_length=10, default="system")  # light/dark/system

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{getattr(self.user, 'email', self.user)} settings"

@receiver(post_save, sender=Profile)
def _update_settings_currency(sender, instance, **kwargs):
    """
    Keep the related Settings.currency in line with the profile's nationality.
    (the tests only check for US → USD; extend the map if you need more).
    """
    if not instance.nationality:
        return
    currency_map = {
    "Nigeria": "NGN",
    "United States": "USD",
    "United Kingdom": "GBP",
    "India": "INR",
    "Canada": "CAD",
    "Australia": "AUD",
    "South Africa": "ZAR",
    "Mexico": "MXN",
    "Brazil": "BRL",
    "Italy": "EUR",
    "Germany": "EUR",
    "France": "EUR",
    "Argentina": "ARS",
    "Japan": "JPY",
    "China": "CNY",
    "Ghana": "GHS",
    "Peru": "PEN",
    "Nepal": "NPR", 
    "Egypt": "EGP",
        # add further mappings as required
    }
    new = currency_map.get(instance.nationality)
    if new:
        settings_obj, _ = Settings.objects.get_or_create(user=instance.user)
        if settings_obj.currency != new:
            settings_obj.currency = new
            settings_obj.save()
