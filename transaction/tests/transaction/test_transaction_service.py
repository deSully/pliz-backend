from django.test import TestCase
from transaction.models import WalletBalanceHistory, Wallet, CustomUser, Transaction
from transaction.services.transaction import TransactionService


class TransactionServiceTests(TestCase):
    def setUp(self):
        # Créer un utilisateur fictif et un wallet pour chaque test
        self.user = CustomUser.objects.create(username="test_user", password="password")
        self.wallet = Wallet.objects.create(user=self.user)

        # Créer une transaction fictive
        self.transaction = Transaction.objects.create(amount=100.0, description="Test Transaction", sender=self.wallet)

    def test_debit_wallet(self):

        WalletBalanceHistory.objects.create(
            wallet=self.wallet,
            balance_before=0.00,
            balance_after=500.00,
            transaction=None  # Pas de transaction initiale
        )

        # Appel de la méthode debit_wallet
        new_balance = TransactionService.debit_wallet(self.wallet, 100.0, self.transaction, "Test de débit")

        # Vérification que le solde après débit est correct
        self.assertEqual(new_balance, 400.0)

        # Vérification dans la base de données que l'enregistrement de WalletBalanceHistory a bien été effectué
        balance_history = WalletBalanceHistory.objects.filter(wallet=self.wallet).latest('timestamp')



        self.assertEqual(balance_history.wallet, self.wallet)
        self.assertEqual(balance_history.balance_before, 500.0)
        self.assertEqual(balance_history.balance_after, 400.0)
        self.assertEqual(balance_history.transaction, self.transaction)  # Vérification avec la vraie transaction
        self.assertEqual(balance_history.transaction_type, "debit")
        self.assertEqual(balance_history.description, "Test de débit")

    def test_credit_wallet(self):

        WalletBalanceHistory.objects.create(
            wallet=self.wallet,
            balance_before=0.00,
            balance_after=500.00,
            transaction=None  # Pas de transaction initiale
        )

        # Appel de la méthode credit_wallet
        new_balance = TransactionService.credit_wallet(self.wallet, 100.0, self.transaction, "Test de crédit")

        # Vérification que le solde après crédit est correct
        self.assertEqual(new_balance, 600.0)

        # Vérification dans la base de données que l'enregistrement de WalletBalanceHistory a bien été effectué
        balance_history = WalletBalanceHistory.objects.filter(wallet=self.wallet).latest('timestamp')

        self.assertEqual(balance_history.wallet, self.wallet)
        self.assertEqual(balance_history.balance_before, 500.0)
        self.assertEqual(balance_history.balance_after, 600.0)
        self.assertEqual(balance_history.transaction, self.transaction)  # Vérification avec la vraie transaction
        self.assertEqual(balance_history.transaction_type, "credit")
        self.assertEqual(balance_history.description, "Test de crédit")
