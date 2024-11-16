from django.db import models

from actor.models import CustomUser


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
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_sent'
    )
    receiver = models.ForeignKey(
        CustomUser,
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
        return f"Transaction {self.transaction_type} de {self.sender} à {self.receiver} - {self.amount} - {self.get_status_display()}"

    class Meta:
        ordering = ('-timestamp',)
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

