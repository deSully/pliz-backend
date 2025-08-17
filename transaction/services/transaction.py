from decimal import Decimal

from rest_framework.exceptions import ValidationError

from transaction.models import Transaction, WalletBalanceHistory

import random
import string
from datetime import datetime


class TransactionService:
    @staticmethod
    def check_sufficient_funds(sender_wallet, amount):
        """
        Vérifie que l'envoyeur a suffisamment de fonds en se basant
        sur le dernier solde enregistré dans WalletBalanceHistory.
        """
        try:
            # Récupère le dernier historique de solde pour le portefeuille donné
            last_balance_history = WalletBalanceHistory.objects.filter(
                wallet=sender_wallet
            ).latest("timestamp")
            current_balance = last_balance_history.balance_after
        except WalletBalanceHistory.DoesNotExist:
            # Si aucun historique n'existe, le solde est considéré comme 0
            current_balance = 0.0

        # Vérifie si le solde est suffisant
        if current_balance < amount:
            raise ValidationError(
                detail="Fonds insuffisants.", code="INSUFFICIENT_FUNDS_ERROR"
            )

    @staticmethod
    def debit_wallet(wallet, amount, transaction, description=None):
        """Débite le wallet du montant spécifié et enregistre l'historique."""
        # Récupération du dernier historique de solde
        last_history = WalletBalanceHistory.objects.filter(wallet=wallet).latest(
            "timestamp"
        )
        if not last_history:
            balance_after = - Decimal(amount)

        else:
            balance_after = last_history.balance_after - Decimal(amount)

        # Enregistrement dans WalletBalanceHistory
        WalletBalanceHistory.objects.create(
            wallet=wallet,
            balance_before=last_history.balance_after,
            balance_after=balance_after,
            transaction=transaction,
            transaction_type="debit",
            description=description,
        )

        return balance_after

    @staticmethod
    def credit_wallet(wallet, amount, transaction, description=None):
        """Crédite le wallet du montant spécifié et enregistre l'historique."""
        # Récupération du dernier historique de solde
        last_history = WalletBalanceHistory.objects.filter(wallet=wallet).latest(
            "timestamp"
        )

        if not last_history:
            balance_after = Decimal(amount)

        else:
            balance_after = last_history.balance_after + Decimal(amount)

        # Enregistrement dans WalletBalanceHistory
        WalletBalanceHistory.objects.create(
            wallet=wallet,
            balance_before=last_history.balance_after,
            balance_after=balance_after,
            transaction=transaction,
            transaction_type="credit",
            description=description,
        )
        return balance_after

    @staticmethod
    def create_pending_transaction(
        sender_wallet,
        receiver_wallet,
        transaction_type,
        amount,
        description=None,
        order_id=None,
    ):
        return Transaction.objects.create(
            sender=sender_wallet,
            receiver=receiver_wallet,
            amount=amount,
            transaction_type=transaction_type,
            status="pending",
            description=description,
            order_id=order_id or TransactionService.generate_order_id(),
        )

    @staticmethod
    def update_transaction_status(transaction, status):
        transaction.status = status
        transaction.save()
        return transaction

    @staticmethod
    def generate_order_id(partner: str = None):
        """
        Génère un order_id unique pour un partenaire donné.
        Si partner n'est pas fourni, utilise 'PLZ' par défaut.
        Format : PARTNER-YYYYMMDD-XXX-XXX-XXX
        """
        partner_code = partner.upper() if partner else "PLZ"
        date_str = datetime.now().strftime("%Y%m%d")
        random_digits1 = f"{random.randint(100, 999)}"
        random_digits2 = f"{random.randint(100, 999)}"
        random_letters = "".join(random.choices(string.ascii_uppercase, k=3))
        return f"{partner_code}-{date_str}-{random_digits1}-{random_digits2}-{random_letters}"
