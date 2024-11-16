from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPES = [
        ('user', 'Utilisateur Normal'),
        ('merchant', 'Marchand'),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='user')


class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wallet')
    phone_number = models.CharField(max_length=15, unique=True)
    currency = models.CharField(max_length=10, default='XOF')  # Adapté pour les CFA, par exemple

    def __str__(self):
        return f"Wallet de {self.user.username} - Solde: {self.balance}"

class Merchant(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='merchant_profile')
    merchant_code = models.CharField(max_length=15, unique=True)
    business_name = models.CharField(max_length=255)
    address = models.TextField()


    def __str__(self):
        return f"Marchand: {self.user.username} - Code: {self.merchant_code}"
