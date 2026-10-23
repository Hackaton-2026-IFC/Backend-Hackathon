from django.conf import settings
from django.db import models

class GoogleIdentity(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='google_identity')
    sub = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
