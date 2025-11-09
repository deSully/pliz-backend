from transaction.errors import PaymentProcessingError
from transaction.merchants.factory import MerchantPaymentFactory

from django.db import transaction as tr

from transaction.services.transaction import TransactionService
from transaction.services.fee import FeeService

from transaction.models import TransactionStatus, TransactionType

import logging

logger = logging.getLogger(__name__)


class MerchantPaymentService:
    @staticmethod
    @tr.atomic
    def process_payment(merchant, sender_wallet, amount, details):
        """
        Traite un paiement marchand. Le client est débité et le marchand crédité
        après validation du paiement via l'API spécifique au marchand.
        
        Supporte 2 cas:
        - Services API (woyofal, rapido, airtime): Appel API externe
        - Marchands Pliz (MCHxxxxx): Paiement direct
        """
        try:
            TransactionService.check_sufficient_funds(sender_wallet, amount)

            description = f"Paiement au marchand {merchant.merchant_code}"

            logger.info(
                f"Initiating payment to merchant {merchant.merchant_code} for amount {amount}"
            )

            transaction = TransactionService.create_pending_transaction(
                sender_wallet,
                merchant.wallet,
                TransactionType.PAYMENT.value,
                amount,
                description,
            )

            logger.info(
                f"Pending transaction created with ID {transaction.order_id} for merchant {merchant.merchant_code}"
            )

            # Vérifier si c'est un service API (woyofal, rapido, airtime) ou un marchand Pliz
            is_api_service = merchant.merchant_code.lower() in ["airtime", "woyofal", "rapido"]
            
            if is_api_service:
                # Cas 1: Service API - Appel externe
                logger.info(f"Processing API service payment for {merchant.merchant_code}")
                payment_processor = MerchantPaymentFactory.get_merchant_processor(
                    merchant.merchant_code
                )

                logger.info(
                    f"Using payment processor {payment_processor.__class__.__name__} for merchant {merchant.merchant_code}"
                )
                response = payment_processor.initiate_payment(transaction, details)
                logger.info(
                    f"Payment processor response for transaction ID {transaction.order_id}: {response}"
                )
                status = response.get("data", {}).get("status")
                if status not in ["success", "pending"]:
                    raise PaymentProcessingError(
                        detail="Le traitement du paiement a échoué.",
                        code="PAYMENT_PROCESSING_ERROR",
                    )
            else:
                # Cas 2: Marchand Pliz - Paiement direct (pas d'API externe)
                logger.info(f"Processing direct merchant payment for {merchant.merchant_code}")
                response = {
                    "status": "success",
                    "data": {
                        "order_id": transaction.order_id,
                        "amount": float(amount),
                        "merchant_code": merchant.merchant_code,
                        "merchant_name": merchant.business_name  # Info bonus utile
                    }
                }
            
            # Créditer le marchand et débiter le client
            TransactionService.credit_wallet(
                merchant.wallet, amount, transaction, description
            )
            TransactionService.debit_wallet(
                sender_wallet, amount, transaction, description
            )
            TransactionService.update_transaction_status(
                transaction, TransactionStatus.SUCCESS.value
            )
            
            # Appliquer les frais après confirmation du succès
            FeeService.apply_fee(
                user=sender_wallet.user,
                wallet=sender_wallet,
                transaction=transaction,
                transaction_type=TransactionType.PAYMENT.value,
                merchant=merchant
            )

            return response

        except PaymentProcessingError:
            raise PaymentProcessingError(
                detail="Le traitement du paiement a échoué.",
                code="PAYMENT_PROCESSING_ERROR",
            )
