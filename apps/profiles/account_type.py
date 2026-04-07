from django.db import models

ACCOUNT_TYPES = (
    ("INDIVIDUAL", "Individual"),
    ("FAMILY", "Family"),
    ("BUSINESS", "Business"),
)

account_type = models.CharField(
    max_length=20,
    choices=ACCOUNT_TYPES,
    default="INDIVIDUAL"
)

PLANS = (
    ("FREE", "Free"),
    ("PLUS", "Plus"),
    ("PRO", "Pro"),
)

plan = models.CharField(max_length=10, choices=PLANS, default="FREE")
