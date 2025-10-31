from decimal import Decimal

from rest_framework.exceptions import ValidationError

from transaction.models import Transaction, WalletBalanceHistory, TransactionStatus
from services.mqtt import mqtt_service

import random
import string
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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
            logger.warning(
                f"No balance history found for wallet {sender_wallet.phone_number}. "
                f"Current balance set to 0."
            )

        # Vérifie si le solde est suffisant
        if current_balance < amount:
            logger.warning(
                f"INSUFFICIENT_FUNDS: Wallet {sender_wallet.phone_number} "
                f"attempted transaction of {amount} {sender_wallet.currency} "
                f"with balance {current_balance} {sender_wallet.currency}"
            )
            raise ValidationError(
                detail="Fonds insuffisants.", code="INSUFFICIENT_FUNDS_ERROR"
            )

    @staticmethod
    def debit_wallet(wallet, amount, transaction, description=None):
        """Débite le wallet du montant spécifié et enregistre l'historique."""

        last_history = None
        balance_after = 0
        balance_before = 0
        try:
            last_history = WalletBalanceHistory.objects.filter(wallet=wallet).latest(
                "timestamp"
            )
            balance_before = last_history.balance_after
            balance_after = last_history.balance_after - Decimal(amount)
        except WalletBalanceHistory.DoesNotExist:
            balance_after = -Decimal(amount)

        # Enregistrement dans WalletBalanceHistory
        WalletBalanceHistory.objects.create(
            wallet=wallet,
            balance_before=balance_before,
            balance_after=balance_after,
            transaction=transaction,
            transaction_type="debit",
            description=description,
        )

        return balance_after

    @staticmethod
    def credit_wallet(wallet, amount, transaction, description=None):
        """Crédite le wallet du montant spécifié et enregistre l'historique."""

        last_history = None
        balance_after = 0
        balance_before = 0
        try:
            last_history = WalletBalanceHistory.objects.filter(wallet=wallet).latest(
                "timestamp"
            )

            balance_before = last_history.balance_after
            balance_after = last_history.balance_after + Decimal(amount)

        except WalletBalanceHistory.DoesNotExist:
            balance_after = Decimal(amount)

        # Enregistrement dans WalletBalanceHistory
        WalletBalanceHistory.objects.create(
            wallet=wallet,
            balance_before=balance_before,
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
        transaction = Transaction.objects.create(
            sender=sender_wallet,
            receiver=receiver_wallet,
            amount=amount,
            transaction_type=transaction_type,
            status=TransactionStatus.PENDING.value,
            description=description,
            order_id=order_id or TransactionService.generate_order_id(),
        )
        
        logger.info(
            f"TRANSACTION_CREATED: {transaction.order_id} | "
            f"Type: {transaction_type} | Amount: {amount} | "
            f"From: {sender_wallet.phone_number if sender_wallet else 'N/A'} | "
            f"To: {receiver_wallet.phone_number if receiver_wallet else 'N/A'}"
        )
        
        return transaction

    @staticmethod
    def update_transaction_status(transaction, status):
        old_status = transaction.status
        transaction.status = status.upper()
        transaction.save()
        
        logger.info(
            f"TRANSACTION_STATUS_CHANGED: {transaction.order_id} | "
            f"{old_status} -> {status.upper()} | "
            f"Amount: {transaction.amount} | "
            f"Type: {transaction.transaction_type}"
        )
        
        # Envoi des notifications MQTT selon le statut
        TransactionService._send_status_notifications(transaction, status)
        
        return transaction
    
    @staticmethod
    def _send_status_notifications(transaction, status):
        """Envoie les notifications MQTT aux utilisateurs concernés"""
        status_upper = status.upper()
        
        # Notification pour le sender
        if transaction.sender and hasattr(transaction.sender.user, 'uuid'):
            sender_uuid = str(transaction.sender.user.uuid)
            
            if status_upper == TransactionStatus.SUCCESS.value:
                if transaction.transaction_type == "TOPUP":
                    mqtt_service.publish_notification(
                        user_uuid=sender_uuid,
                        notification_type="topup_success",
                        title="✅ Recharge réussie",
                        message=f"Votre compte a été rechargé de {transaction.amount} FCFA",
                        data={
                            "transaction_id": transaction.order_id,
                            "amount": float(transaction.amount),
                            "type": transaction.transaction_type
                        }
                    )
                else:
                    mqtt_service.publish_notification(
                        user_uuid=sender_uuid,
                        notification_type="transaction_success",
                        title="✅ Envoi réussi",
                        message=f"Envoi de {transaction.amount} FCFA à {transaction.receiver.phone_number} réussi",
                        data={
                            "transaction_id": transaction.order_id,
                            "amount": float(transaction.amount),
                            "receiver": transaction.receiver.phone_number
                        }
                    )
            
            elif status_upper == TransactionStatus.FAILED.value:
                mqtt_service.publish_notification(
                    user_uuid=sender_uuid,
                    notification_type="transaction_failed",
                    title="❌ Transaction échouée",
                    message=f"La transaction de {transaction.amount} FCFA a échoué",
                    data={
                        "transaction_id": transaction.order_id,
                        "amount": float(transaction.amount),
                        "type": transaction.transaction_type
                    }
                )
        
        # Notification pour le receiver
        if transaction.receiver and hasattr(transaction.receiver.user, 'uuid') and status_upper == TransactionStatus.SUCCESS.value:
            receiver_uuid = str(transaction.receiver.user.uuid)
            
            if transaction.transaction_type == "PAYMENT":
                # Notification marchand
                mqtt_service.publish_merchant_notification(
                    merchant_uuid=receiver_uuid,
                    payment_data={
                        "transaction_id": transaction.order_id,
                        "amount": float(transaction.amount),
                        "customer_phone": transaction.sender.phone_number if transaction.sender else "N/A",
                        "description": transaction.description or "",
                        "timestamp": transaction.created_at.isoformat()
                    }
                )
                
                mqtt_service.publish_notification(
                    user_uuid=receiver_uuid,
                    notification_type="payment_received",
                    title="🏪 Paiement reçu",
                    message=f"Vous avez reçu un paiement de {transaction.amount} FCFA",
                    data={
                        "transaction_id": transaction.order_id,
                        "amount": float(transaction.amount),
                        "customer": transaction.sender.phone_number if transaction.sender else "N/A"
                    }
                )
            else:
                # Notification utilisateur normal
                mqtt_service.publish_notification(
                    user_uuid=receiver_uuid,
                    notification_type="money_received",
                    title="💰 Argent reçu",
                    message=f"Vous avez reçu {transaction.amount} FCFA de {transaction.sender.phone_number if transaction.sender else 'un utilisateur'}",
                    data={
                        "transaction_id": transaction.order_id,
                        "amount": float(transaction.amount),
                        "sender": transaction.sender.phone_number if transaction.sender else "N/A"
                    }
                )

    @staticmethod
    def add_additional_data(transaction, data):
        if not transaction.additional_data:
            transaction.additional_data = {}
        transaction.additional_data.update(data)
        transaction.save()
        return transaction
    
    @staticmethod
    def add_external_reference(transaction, reference):
        transaction.external_reference = reference
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
