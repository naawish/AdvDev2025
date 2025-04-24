from django.db import models

# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Make sure this class definition exists and is spelled correctly!
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        DOCTOR = 'DOCTOR', 'Doctor'
        ADMIN_OFFICER = 'ADMIN_OFFICER', 'Administrative Officer'
        MANAGER = 'MANAGER', 'Manager'
        ADMIN = 'ADMIN', 'Admin'

    email = models.EmailField(unique=True) # Ensure email is unique
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)

    USERNAME_FIELD = 'email' # Use email to log in
    REQUIRED_FIELDS = ['username'] # Keep username required for createsuperuser or remove if you don't want it

    def __str__(self):
        return self.get_full_name() or self.email