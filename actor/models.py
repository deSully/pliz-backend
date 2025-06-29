from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

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
    )
    is_platform = models.BooleanField(default=False)

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
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    banque = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=10)
    code_guichet = models.CharField(max_length=10)
    numero_compte = models.CharField(max_length=20)
    cle_rib = models.CharField(max_length=5)
    titulaire = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RIB {self.banque} - {self.numero_compte}"


class Country(models.Model):
    """
    Modèle représentant un pays dans lequel une banque peut être située.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=3, unique=True)  # Code ISO à 3 lettres pour le pays
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Bank(models.Model):
    """
    Modèle représentant une banque.
    La banque est le garant du système et est associée à un pays spécifique.
    """
    name = models.CharField(max_length=255)
    bank_code = models.CharField(max_length=10, unique=True)  # Code unique pour la banque
    bic_code = models.CharField(max_length=20, unique=True)  # Code BIC (pour l'international)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='banques')  # Association à un pays
    address = models.TextField(null=True, blank=True)  # Adresse de la banque (optionnelle)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.bank_code}) - {self.pays.name}"
