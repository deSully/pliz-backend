from unittest.mock import patch, MagicMock
from django.test import TestCase
from decimal import Decimal

from rest_framework.exceptions import ValidationError

from actor.models import CustomUser, Merchant
from transaction.errors import PaymentProcessingError
from transaction.models import Wallet, WalletBalanceHistory
from transaction.merchants.service import MerchantPaymentService
from transaction.services.transaction import TransactionService


class MerchantPaymentServiceTests(TestCase):
    def setUp(self):
        # Configuration des données fictives

        self.sender = CustomUser.objects.create(username="sender")
        self.receiver = CustomUser.objects.create(username="receiver")

        # Création des wallets
        self.sender_wallet = Wallet.objects.create(user=self.sender, phone_number="1234567890")
        self.merchant_wallet = Wallet.objects.create(user=self.receiver, phone_number="0987654321")

        # Création des historiques de solde
        WalletBalanceHistory.objects.create(wallet=self.sender_wallet, balance_before=Decimal(1000.0), balance_after=Decimal(900.0))
        WalletBalanceHistory.objects.create(wallet=self.merchant_wallet, balance_before=Decimal(1000.0), balance_after=Decimal(1100.0))

        # Création merchant
        self.merchant = Merchant.objects.create(merchant_code="TEST", wallet=self.merchant_wallet)

        # Détails du paiement
        self.amount = Decimal(100.0)
        self.details = {"order_id": "ORDER123", "description": "Achat de produit"}


    @patch("transaction.merchants.service.TransactionService")
    @patch("transaction.merchants.factory.MerchantPaymentFactory.get_merchant_processor")
    def test_process_payment_success(self, mock_get_merchant_processor, mock_transaction_service):
        # Configuration du simulateur de traitement du marchand
        mock_processor = MagicMock()
        mock_processor.process_payment.return_value = {"status": "success", "message": "Paiement validé"}
        mock_get_merchant_processor.return_value = mock_processor

        # Simule une transaction fictive renvoyée par TransactionService
        mock_transaction = MagicMock()
        mock_transaction_service.create_pending_transaction.return_value = mock_transaction

        # Appel de la méthode
        response = MerchantPaymentService.process_payment(
            merchant=self.merchant,
            sender_wallet=self.sender_wallet,
            amount=self.amount,
            details=self.details,
        )

        # Vérifications
        mock_transaction_service.check_sufficient_funds.assert_called_once_with(self.sender_wallet, self.amount)
        mock_transaction_service.debit_wallet.assert_called_once_with(
            self.sender_wallet, self.amount, mock_transaction, f"Paiement au marchand {self.merchant.merchant_code}"
        )
        mock_processor.process_payment.assert_called_once_with(self.amount, self.details)
        mock_transaction_service.credit_wallet.assert_called_once_with(
            self.merchant_wallet, self.amount, mock_transaction, f"Paiement au marchand {self.merchant.merchant_code}"
        )
        mock_transaction_service.update_transaction_status.assert_called_once_with(mock_transaction, "success")
        self.assertEqual(response, {"status": "success", "message": "Paiement validé"})

    @patch("transaction.merchants.service.TransactionService")
    def test_process_payment_insufficient_funds(self, mock_transaction_service):
        # Simule une erreur de fonds insuffisants
        mock_transaction_service.check_sufficient_funds.side_effect = ValidationError("Fonds insuffisants.")

        with self.assertRaises(ValidationError) as context:
            MerchantPaymentService.process_payment(
                merchant=self.merchant,
                sender_wallet=self.sender_wallet,
                amount=self.amount,
                details=self.details,
            )

        mock_transaction_service.check_sufficient_funds.assert_called_once_with(self.sender_wallet, self.amount)
        self.assertEqual(str(context.exception.detail[0]), "Fonds insuffisants.")

    @patch("transaction.merchants.factory.MerchantPaymentFactory.get_merchant_processor")
    def test_process_payment_failure_in_merchant_processor(self, mock_get_merchant_processor):
        # Simule une erreur levée par le processeur du marchand
        mock_processor = MagicMock()
        mock_processor.process_payment.side_effect = PaymentProcessingError("Erreur du marchand.")
        mock_get_merchant_processor.return_value = mock_processor

        with self.assertRaises(PaymentProcessingError) as context:
            MerchantPaymentService.process_payment(
                merchant=self.merchant,
                sender_wallet=self.sender_wallet,
                amount=self.amount,
                details=self.details,
            )

        self.assertEqual(str(context.exception.detail),"Le paiement a échoué. Veuillez réessayer plus tard.")

    @patch("transaction.merchants.service.TransactionService")
    def test_process_payment_error_during_debit(self, mock_transaction_service):
        # Simule une erreur pendant le débit du portefeuille
        mock_transaction_service.debit_wallet.side_effect = PaymentProcessingError("Erreur de débit.")

        with self.assertRaises(PaymentProcessingError) as context:
            MerchantPaymentService.process_payment(
                merchant=self.merchant,
                sender_wallet=self.sender_wallet,
                amount=self.amount,
                details=self.details,
            )

        self.assertEqual(str(context.exception.detail), "Le paiement a échoué. Veuillez réessayer plus tard.")
