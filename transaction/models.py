from django.db import models

from actor.models import Wallet
from actor.models import Merchant
from actor.models import Bank

# Create your models here.
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('send', 'Envoi'),
        ('receive', 'Réception'),
        ('payment', 'Paiement Service'),
        
    ]

    TRANSACTION_STATUSES = [
        ('pending', 'En attente'),
        ('completed', 'Réussie'),
        ('failed', 'Échouée'),
        ('cancelled', 'Annulée'),
    ]

    sender = models.ForeignKey(
        Wallet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_sent'
    )
    receiver = models.ForeignKey(
        Wallet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_received'
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUSES, default='pending')

    def __str__(self):
        return f"Transaction {self.transaction_type} de {self.sender} à {self.receiver} - {self.amount}"

    class Meta:
        ordering = ('-timestamp',)
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'


class WalletBalanceHistory(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='wallet_balance_histories')
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE, related_name='balance_histories', null=True)
    description = models.TextField(blank=True, null=True)
    transaction_type = models.CharField(max_length=50, choices=[('send', 'Send'), ('receive', 'Receive')])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Historique du solde - {self.wallet.user.username} - {self.timestamp} - Avant: {self.balance_before}, Après: {self.balance_after}"


class Fee(models.Model):
    TRANSACTION_TYPES = [
        ("send_money", "Envoi d'argent"),
        ("topup", "Rechargement"),
        ("merchant_payment", "Paiement marchand"),
    ]

    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    merchant = models.ForeignKey(Merchant, null=True, blank=True, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, null=True, blank=True, on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        target = self.merchant or self.bank or "Global"
        return f"{self.transaction_type} - {target} ({self.percentage or 0}% + {self.fixed_amount or 0})"
