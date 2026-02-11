from django.db import models
from apps.users.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    currency = models.CharField(max_length=10, default='NGN')
    timezone = models.CharField(max_length=50, default='Africa/Lagos')

    def __str__(self):
        return self.full_name or self.user.emails