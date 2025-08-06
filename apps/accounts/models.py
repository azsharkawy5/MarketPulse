from django.db import models
from django.contrib.auth.models import AbstractUser

class User (AbstractUser):

    email=models.EmailField(max_length=255, unique=True) 
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']