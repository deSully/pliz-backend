from transaction.errors import PaymentProcessingError
from transaction.merchants.factory import MerchantPaymentFactory

from django.db import transaction as tr

from transaction.services.transaction import TransactionService

from transaction.models import TransactionStatus

import logging

logger = logging.getLogger(__name__)


class MerchantPaymentService:
    @staticmethod
    def process_payment(merchant, sender_wallet, amount, details):
        """
        Traite un paiement marchand. Le client est débité et le marchand crédité
        après validation du paiement via l'API spécifique au marchand.
        """
        try:
            with tr.atomic():
                TransactionService.check_sufficient_funds(sender_wallet, amount)

                description = f"Paiement au marchand {merchant.merchant_code}"

                logger.info(
                    f"Initiating payment to merchant {merchant.merchant_code} for amount {amount}"
                )

                transaction = TransactionService.create_pending_transaction(
                    sender_wallet, merchant.wallet, "payment", amount, description
                )

                logger.info(
                    f"Pending transaction created with ID {transaction.order_id} for merchant {merchant.merchant_code}"
                )

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
                if status != "success":
                    raise PaymentProcessingError(
                        detail="Le traitement du rechargement a échoué.",
                        code="PAYMENT_PROCESSING_ERROR",
                    )
                TransactionService.credit_wallet(
                    merchant.wallet, amount, transaction, description
                )
                TransactionService.debit_wallet(
                    sender_wallet, amount, transaction, description
                )
                TransactionService.update_transaction_status(
                    transaction, TransactionStatus.SUCCESS.value
                )

                return response

        except PaymentProcessingError:
            raise PaymentProcessingError(
                detail="Le traitement du rechargement a échoué.",
                code="PAYMENT_PROCESSING_ERROR",
            )
