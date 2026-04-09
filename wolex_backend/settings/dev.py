from .base import *

DEBUG = True
ALLOWED_HOSTS = []

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"



from django.core.management.utils import get_random_secret_key

print(get_random_secret_key())