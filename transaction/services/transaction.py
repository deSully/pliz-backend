from decimal import Decimal

from rest_framework.exceptions import ValidationError

from transaction.models import Transaction, WalletBalanceHistory

class TransactionService:
    @staticmethod
    def check_sufficient_funds(sender_wallet, amount):
        """
        Vérifie que l'envoyeur a suffisamment de fonds en se basant
        sur le dernier solde enregistré dans WalletBalanceHistory.
        """
        try:
            # Récupère le dernier historique de solde pour le portefeuille donné
            last_balance_history = WalletBalanceHistory.objects.filter(wallet=sender_wallet).latest('timestamp')
            current_balance = last_balance_history.balance_after
        except WalletBalanceHistory.DoesNotExist:
            # Si aucun historique n'existe, le solde est considéré comme 0
            current_balance = 0.0

        # Vérifie si le solde est suffisant
        if current_balance < amount:
            raise ValidationError("Fonds insuffisants.")

    @staticmethod
    def debit_wallet(wallet, amount, transaction, description=None):
        """Débite le wallet du montant spécifié et enregistre l'historique."""
        # Récupération du dernier historique de solde
        last_history = WalletBalanceHistory.objects.filter(wallet=wallet).latest('timestamp')

        # Nouveau solde
        balance_after = last_history.balance_after - Decimal(amount)

        # Enregistrement dans WalletBalanceHistory
        WalletBalanceHistory.objects.create(
            wallet=wallet,
            balance_before=last_history.balance_after,
            balance_after=balance_after,
            transaction=transaction,
            transaction_type="debit",
            description=description
        )

        return balance_after

    @staticmethod
    def credit_wallet(wallet, amount, transaction, description=None):
        """Crédite le wallet du montant spécifié et enregistre l'historique."""
        # Récupération du dernier historique de solde
        last_history = WalletBalanceHistory.objects.filter(wallet=wallet).latest('timestamp')

        # Nouveau solde
        balance_after = last_history.balance_after + Decimal(amount)

        # Enregistrement dans WalletBalanceHistory
        WalletBalanceHistory.objects.create(
            wallet=wallet,
            balance_before=last_history.balance_after,
            balance_after=balance_after,
            transaction=transaction,
            transaction_type="credit",
            description=description
        )
        return balance_after

    @staticmethod
    def create_pending_transaction(sender_wallet, receiver_wallet, transaction_type, amount, description=None):
        return Transaction.objects.create(
            sender=sender_wallet,
            receiver=receiver_wallet,
            amount=amount,
            transaction_type=transaction_type,
            status='pending',
            description=description,
        )

    @staticmethod
    def update_transaction_status(transaction, status):
        transaction.status = status
        transaction.save()
        return transaction