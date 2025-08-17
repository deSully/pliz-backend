from transaction.errors import PaymentProcessingError
from transaction.merchants.factory import MerchantPaymentFactory

from django.db import transaction as tr

from transaction.services.transaction import TransactionService


class MerchantPaymentService:
    @staticmethod
    def process_payment(merchant, sender_wallet, amount, details):
        """
        Traite un paiement marchand. Le client est débité et le marchand crédité
        après validation du paiement via l'API spécifique au marchand.
        """
        try:
            # 1. Début de la transaction atomique pour la cohérence des données
            with tr.atomic():
                # 2. Vérifier si le client a suffisamment de fonds
                TransactionService.check_sufficient_funds(sender_wallet, amount)

                # 3. Créer une transaction en attente
                description = f"Paiement au marchand {merchant.merchant_code}"
                transaction = TransactionService.create_pending_transaction(
                    sender_wallet, merchant.wallet, "payment", amount, description
                )

                # 4. Débiter le client
                TransactionService.debit_wallet(
                    sender_wallet, transaction.amount, transaction, description
                )

                # 5. Processus spécifique au marchand
                payment_processor = MerchantPaymentFactory.get_merchant_processor(
                    merchant
                )
                response = payment_processor.process_payment(amount, details)
                TransactionService.credit_wallet(
                    merchant.wallet, amount, transaction, description
                )
                TransactionService.update_transaction_status(transaction, "success")

                return response

        except PaymentProcessingError:
            raise PaymentProcessingError(
                "Le paiement a échoué. Veuillez réessayer plus tard."
            )
