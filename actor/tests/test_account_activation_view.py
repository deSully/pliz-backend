from rest_framework import status
from rest_framework.test import APITestCase
from actor.models import CustomUser
from services.otp import OTPService
from unittest.mock import patch
from rest_framework.exceptions import ValidationError
from django.urls import reverse

class UserAccountActivationViewTest(APITestCase):
    """
    Tests pour activer un compte utilisateur via un OTP et un numéro de téléphone.
    """
    def setUp(self):
        self.url = reverse('user-account-activation')  # URL de la vue d'activation

    @patch('services.otp.OTPService.validate_otp')  # On simule la validation de l'OTP
    def test_account_activation_success(self, mock_validate_otp):
        """
        Teste l'activation d'un compte avec un OTP valide.
        """
        # Créer un utilisateur avec un téléphone et un compte non actif
        user = CustomUser.objects.create_user(
            username='1234567890',
            email='user@example.com',
            first_name='John',
            last_name='Doe',
            is_active=False
        )

        # Simuler la validation de l'OTP
        mock_validate_otp.return_value = True

        # Données d'activation
        data = {
            'phone_number': '1234567890',
            'otp': '123456'  # L'OTP simulé
        }

        # Envoyer la requête POST
        response = self.client.post(self.url, data, format='json')

        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que l'utilisateur est bien activé
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    @patch('services.otp.OTPService.validate_otp')  # On simule la validation de l'OTP
    def test_account_activation_invalid_otp(self, mock_validate_otp):
        """
        Teste l'activation d'un compte avec un OTP invalide.
        """
        # Créer un utilisateur avec un téléphone et un compte non actif
        user = CustomUser.objects.create_user(
            username='1234567890',
            email='user@example.com',
            first_name='John',
            last_name='Doe',
            is_active=False
        )

        # Simuler l'OTP invalide
        mock_validate_otp.return_value = False

        # Données d'activation avec OTP invalide
        data = {
            'phone_number': '1234567890',
            'otp': 'wrong-otp'
        }

        # Envoyer la requête POST
        response = self.client.post(self.url, data, format='json')

        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('services.otp.OTPService.validate_otp')  # On simule la validation de l'OTP
    def test_account_activation_user_already_active(self, mock_validate_otp):
        """
        Teste l'activation d'un compte déjà actif.
        """
        # Créer un utilisateur avec un téléphone et un compte actif
        CustomUser.objects.create_user(
            username='1234567890',
            email='user@example.com',
            first_name='John',
            last_name='Doe',
            is_active=True
        )

        # Simuler la validation de l'OTP
        mock_validate_otp.return_value = True

        # Données d'activation pour un compte déjà actif
        data = {
            'phone_number': '1234567890',
            'otp': '123456'  # L'OTP simulé
        }

        # Envoyer la requête POST
        response = self.client.post(self.url, data, format='json')

        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('services.otp.OTPService.validate_otp')  # On simule la validation de l'OTP
    def test_account_activation_user_not_found(self, mock_validate_otp):
        """
        Teste l'activation d'un compte avec un numéro de téléphone non trouvé.
        """
        # Simuler la validation de l'OTP
        mock_validate_otp.return_value = True

        # Données d'activation avec un numéro de téléphone non existant
        data = {
            'phone_number': 'nonexistent_phone',
            'otp': '123456'
        }

        # Envoyer la requête POST
        response = self.client.post(self.url, data, format='json')

        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
