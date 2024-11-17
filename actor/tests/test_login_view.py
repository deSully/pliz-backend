# tests.py
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from actor.models import CustomUser
from django.urls import reverse
from services.otp import OTPService

class UserLoginViewTest(APITestCase):
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = CustomUser.objects.create(username="1234567890")

        # URL de l'API
        self.url = reverse('login')  # Assurez-vous que cette URL est correctement configurée dans vos URLs

        # Simuler l'envoi de l'OTP
        self.otp = '123456'  # OTP fictif pour les tests

        # Générer un OTP valide pour l'utilisateur
        with patch('services.otp.OTPService.generate_otp') as mock_generate_otp:
            mock_generate_otp.return_value = self.otp
            OTPService.generate_otp(self.user)

    @patch('services.otp.OTPService.validate_otp')
    def test_login_with_valid_otp(self, mock_validate_otp):
        # Le mock de validate_otp doit retourner True
        mock_validate_otp.return_value = True

        # Appel de l'API avec un OTP valide
        data = {
            'phone_number': '1234567890',
            'otp': self.otp
        }
        response = self.client.post(self.url, data)

        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_validate_otp.assert_called_once_with(self.user, self.otp)

    @patch('services.otp.OTPService.validate_otp')
    def test_login_with_invalid_otp(self, mock_validate_otp):
        # Le mock de validate_otp doit retourner False pour simuler un OTP invalide
        mock_validate_otp.return_value = False

        # Appel de l'API avec un OTP invalide
        data = {
            'phone_number': '1234567890',
            'otp': '000000'  # OTP incorrect
        }
        response = self.client.post(self.url, data)

        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_validate_otp.assert_called_once_with(self.user, '000000')  # Vérifie que validate_otp a été appelé avec les bons arguments

    @patch('actor.models.CustomUser.objects.get')
    def test_login_with_nonexistent_user(self, mock_get):
        # Le mock doit simuler une exception DoesNotExist pour un utilisateur inexistant
        mock_get.side_effect = CustomUser.DoesNotExist

        # Appel de l'API avec un numéro de téléphone inexistant
        data = {
            'phone_number': '0987654321',  # Numéro de téléphone inexistant
            'otp': self.otp
        }
        response = self.client.post(self.url, data)

        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_get.assert_called_once_with(username='0987654321')  # Vérifie que la méthode get a été appelée avec le bon numéro de téléphone


    @patch('services.otp.OTPService.validate_otp')
    @patch('services.token.TokenService.generate_tokens_for_user')
    def test_login_generates_tokens(self, mock_generate_tokens, mock_validate_otp):
        # Le mock de validate_otp doit retourner True
        mock_validate_otp.return_value = True

        # Le mock de generate_tokens doit retourner des tokens fictifs
        mock_generate_tokens.return_value = {
            "refresh": "mock_refresh_token",
            "access": "mock_access_token"
        }

        # Appel de l'API avec un OTP valide
        data = {
            'phone_number': '1234567890',
            'otp': self.otp
        }
        response = self.client.post(self.url, data)

        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_validate_otp.assert_called_once_with(self.user, self.otp)
        mock_generate_tokens.assert_called_once_with(self.user)

        # Vérifie que les tokens sont dans la réponse
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['tokens']['refresh'], "mock_refresh_token")
        self.assertEqual(response.data['tokens']['access'], "mock_access_token")
