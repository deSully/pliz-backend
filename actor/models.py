from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    USER_TYPES = [
        ("user", "Utilisateur Normal"),
        ("merchant", "Marchand"),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default="user")
    is_subscribed = models.BooleanField(default=False)


class Wallet(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="wallet"
    )
    phone_number = models.CharField(max_length=15, unique=True)
    currency = models.CharField(
        max_length=10, default="XOF"
    )  # Adapté pour les CFA, par exemple

    def __str__(self):
        return f"Wallet de {self.user.username} - {self.phone_number} - {self.currency}"


class Merchant(models.Model):
    wallet = models.OneToOneField(
        Wallet, on_delete=models.CASCADE, related_name="merchant_wallet", null=True
    )
    merchant_code = models.CharField(max_length=15, unique=True)
    business_name = models.CharField(max_length=255)
    address = models.TextField()

    def __str__(self):
        return f"Marchand: {self.wallet.user.username} - Code: {self.merchant_code}"


class RIB(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="ribs")
    banque = models.CharField(max_length=100)
    code_banque = models.CharField(max_length=10)
    code_guichet = models.CharField(max_length=10)
    numero_compte = models.CharField(max_length=20)
    cle_rib = models.CharField(max_length=5)
    titulaire = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RIB {self.banque} - {self.numero_compte}"
