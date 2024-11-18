from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from actor.models import CustomUser, Wallet
from transaction.models import WalletBalanceHistory
from services.token import TokenService


class SendMoneyViewTest(APITestCase):
    def setUp(self):
        # Création des utilisateurs
        self.sender = CustomUser.objects.create(username="sender")
        self.receiver = CustomUser.objects.create(username="receiver")

        # Création des wallets
        self.sender_wallet = Wallet.objects.create(user=self.sender, phone_number="1234567890")
        self.receiver_wallet = Wallet.objects.create(user=self.receiver, phone_number="0987654321")

        # Création des historiques de solde
        WalletBalanceHistory.objects.create(
            wallet=self.sender_wallet,
            balance_before=0.00,
            balance_after=100.00,
            transaction=None  # Pas de transaction initiale
        )
        WalletBalanceHistory.objects.create(
            wallet=self.receiver_wallet,
            balance_before=0.00,
            balance_after=50.00,
            transaction=None  # Pas de transaction initiale
        )

        # URL de l'API
        self.url = reverse('send-money')

        # Générer le token pour l'envoyeur (sender) et l'authentifier
        self.token = TokenService.generate_tokens_for_user(self.sender)["access"]
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def get_wallet_balance(self, wallet):
        # Calculer le solde actuel en récupérant le dernier historique
        last_history = WalletBalanceHistory.objects.filter(wallet=wallet).latest('timestamp')
        return last_history.balance_after

    def test_unauthenticated_user(self):
        data = {
            'receiver': self.receiver.id,
            'transaction_type': 'send',
            'amount': 50.00,
            'description': 'Paiement test'
        }

        # Supprimer le token (si configuré dans le setUp)
        self.client.credentials()  # Réinitialise les headers pour la requête actuelle

        # Envoi de la requête sans le header d'autorisation
        response = self.client.post(self.url, data)

        # Vérification du code de réponse
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Vérification du message d'erreur
        self.assertIn('Authentication credentials were not provided.', response.data['detail'])


    def test_send_money_success(self):
        data = {
            'receiver': self.receiver.id,
            'transaction_type': 'send',
            'amount': 30.00,
            'description': 'Paiement test'
        }

        # Envoi de la requête POST
        response = self.client.post(self.url, data)

        # Vérification de la réponse
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérification des soldes mis à jour
        self.sender_wallet.refresh_from_db()
        self.receiver_wallet.refresh_from_db()

        # Récupérer les soldes après la transaction
        sender_balance = self.get_wallet_balance(self.sender_wallet)
        receiver_balance = self.get_wallet_balance(self.receiver_wallet)

        # Vérifier si les soldes sont corrects
        self.assertEqual(sender_balance, 70.00)
        self.assertEqual(receiver_balance, 80.00)

        # Vérification de l'historique des soldes
        history_sender = WalletBalanceHistory.objects.filter(wallet=self.sender_wallet).latest('timestamp')
        history_receiver = WalletBalanceHistory.objects.filter(wallet=self.receiver_wallet).latest('timestamp')

        self.assertEqual(history_sender.balance_before, 100.00)
        self.assertEqual(history_sender.balance_after, 70.00)
        self.assertEqual(history_receiver.balance_before, 50.00)
        self.assertEqual(history_receiver.balance_after, 80.00)

    def test_insufficient_funds(self):
        data = {
            'receiver': self.receiver.id,
            'transaction_type': 'send',
            'amount': 200.00,  # Montant supérieur au solde de l'envoyeur
            'description': 'Paiement test'
        }
        # Envoi de la requête POST
        response = self.client.post(self.url, data)

        # Vérification de la réponse
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Vérification de l'erreur
        errors = response.data['non_field_errors']
        self.assertTrue(any("Fonds insuffisants" in str(error) for error in errors))
