import json

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from actor.models import CustomUser, Wallet, Merchant
from transaction.models import WalletBalanceHistory
from transaction.errors import PaymentProcessingError
from services.token import TokenService
from transaction.merchants.service import MerchantPaymentService
from unittest.mock import patch

class MerchantPaymentViewTest(APITestCase):

    def setUp(self):
        # Création des utilisateurs
        self.sender = CustomUser.objects.create(username="sender")
        self.receiver = CustomUser.objects.create(username="receiver")

        # Création des wallets
        self.sender_wallet = Wallet.objects.create(user=self.sender, phone_number="1234567890")
        self.receiver_wallet = Wallet.objects.create(user=self.receiver, phone_number="0987654321")

        # Historique des soldes
        WalletBalanceHistory.objects.create(
            wallet=self.sender_wallet,
            balance_before=0.00,
            balance_after=1000.00,
            transaction=None  # Pas de transaction initiale
        )
        WalletBalanceHistory.objects.create(
            wallet=self.receiver_wallet,
            balance_before=0.00,
            balance_after=500.00,
            transaction=None  # Pas de transaction initiale
        )

        # Créer un marchand
        self.merchant = Merchant.objects.create(merchant_code='MERCH_001', wallet=self.receiver_wallet)

        # URL de l'API
        self.url = reverse('merchant-payment')
        self.data = {
            'merchant_code': 'MERCH_001',
            'amount': 100.00,
            'details': {'order_id': 'ORDER123', 'description': 'Achat de produit'}
        }

        # Générer le token pour l'envoyeur (sender) et l'authentifier
        self.token = TokenService.generate_tokens_for_user(self.sender)["access"]
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def get_wallet_balance(self, wallet):
        # Calculer le solde actuel en récupérant le dernier historique
        last_history = WalletBalanceHistory.objects.filter(wallet=wallet).latest('timestamp')
        return last_history.balance_after

    def test_unauthenticated_user(self):


        # Supprimer le token (si configuré dans le setUp)
        self.client.credentials()  # Réinitialise les headers pour la requête actuelle

        # Envoi de la requête sans le header d'autorisation
        response = self.client.post(self.url, self.data, format='json')

        # Vérification du code de réponse
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Vérification du message d'erreur
        self.assertIn('Authentication credentials were not provided.', response.data['detail'])

    def test_successful_payment(self):


        # Envoi de la requête POST
        with patch.object(MerchantPaymentService, 'process_payment', return_value={'message': 'Paiement effectué avec succès', 'transaction_id': 123}):
            response = self.client.post(self.url, self.data, format='json')

        # Vérification de la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Paiement effectué avec succès')
        self.assertEqual(response.data['transaction_id'], 123)

        # Vérification des soldes mis à jour
        self.sender_wallet.refresh_from_db()
        self.receiver_wallet.refresh_from_db()

        sender_balance = self.get_wallet_balance(self.sender_wallet)
        receiver_balance = self.get_wallet_balance(self.receiver_wallet)

        print(sender_balance)
        print(receiver_balance)

        self.assertEqual(sender_balance, 1000.00)
        self.assertEqual(receiver_balance, 500.00)



    def test_insufficient_funds(self):

        # Envoi de la requête POST
        with patch.object(MerchantPaymentService, 'process_payment', side_effect=PaymentProcessingError("Fonds insuffisants.")):
            response = self.client.post(self.url, self.data, format='json')

        # Vérification de la réponse
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_invalid_merchant_code(self):
        self.data['merchant_code'] = 'INVALID_CODE'

        response = self.client.post(self.url, self.data, format='json')

        # Vérification de la réponse d'erreur pour code marchand invalide
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_required_fields(self):
        del self.data['amount']

        response = self.client.post(self.url, self.data, format='json')

        # Vérification de la réponse d'erreur pour les champs manquants
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unexpected_error(self):

        # Mock une exception générique
        with patch.object(MerchantPaymentService, 'process_payment', side_effect=Exception("Erreur inattendue.")):
            response = self.client.post(self.url, self.data, format='json')

        # Vérifie la réponse d'erreur générique
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
