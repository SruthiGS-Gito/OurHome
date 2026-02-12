from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    # Custom user model for OurHome
    
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('contractor', 'Contractor'),
        ('designer', 'Designer'),
        ('shop_owner', 'Shop Owner'),
    ]
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    
    USERNAME_FIELD = 'email'  # Login with email instead of username
    REQUIRED_FIELDS = ['username', 'phone']
    
    def __str__(self):
        return self.email