from rest_framework.test import APITestCase
from rest_framework import status

from services.token import TokenService
from transaction.models import  Transaction, WalletBalanceHistory
from actor.models import Wallet, CustomUser

from django.urls import reverse

class TransactionHistoryViewTest(APITestCase):

    def setUp(self):
        # Créer des utilisateurs
        self.user1 = CustomUser.objects.create_user(username='user1', password='password123')
        self.user2 = CustomUser.objects.create_user(username='user2', password='password123')

        # Créer des portefeuilles
        self.wallet1 = Wallet.objects.create(user=self.user1, phone_number="1234567890")
        self.wallet2 = Wallet.objects.create(user=self.user2, phone_number="0987654321")

        # Créer des transactions
        self.transaction1 = Transaction.objects.create(
            sender=self.wallet1,
            receiver=self.wallet2,
            transaction_type='send',
            amount=100.00,
            status='completed',
            description="Envoi de fonds"
        )
        self.transaction2 = Transaction.objects.create(
            sender=self.wallet2,
            receiver=self.wallet1,
            transaction_type='receive',
            amount=50.00,
            status='completed',
            description="Réception de fonds"
        )

        # Créer des historiques de solde
        WalletBalanceHistory.objects.create(
            wallet=self.wallet1,
            balance_before=1000.00,
            balance_after=900.00,
            transaction=self.transaction1,
            transaction_type='send'
        )
        WalletBalanceHistory.objects.create(
            wallet=self.wallet2,
            balance_before=500.00,
            balance_after=600.00,
            transaction=self.transaction1,
            transaction_type='receive'
        )
        WalletBalanceHistory.objects.create(
            wallet=self.wallet2,
            balance_before=600.00,
            balance_after=550.00,
            transaction=self.transaction2,
            transaction_type='send'
        )
        WalletBalanceHistory.objects.create(
            wallet=self.wallet1,
            balance_before=900.00,
            balance_after=950.00,
            transaction=self.transaction2,
            transaction_type='receive'
        )

        self.url = reverse('transaction-history')

        # Générer le token pour l'envoyeur (sender) et l'authentifier
        self.token = TokenService.generate_tokens_for_user(self.user1)["access"]
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_transaction_history_authenticated_user(self):

        # Faire une requête à l'API
        response = self.client.get(self.url)

        # Vérifier le statut de la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier les données retournées
        self.assertEqual(len(response.data), 2)  # Deux transactions

    def test_transaction_history_unauthenticated_user(self):
        # Requête sans authentification
        self.client.credentials()
        response = self.client.get(self.url)

        # Vérifier que l'utilisateur non authentifié est refusé
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_transaction_history_other_user(self):

        # Faire une requête à l'API
        response = self.client.get(self.url)

        # Vérifier le statut de la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier les données retournées pour l'utilisateur 2
        self.assertEqual(len(response.data), 2)  # Deux transactions
