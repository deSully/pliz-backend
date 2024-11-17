from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from actor.models import CustomUser
from django.urls import reverse

class SendOTPViewTest(APITestCase):
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = CustomUser.objects.create_user(
            username='1234567890',
            email='user@example.com',
            first_name='John',
            last_name='Doe',
            is_active=True
        )  # Exemple de numéro de téléphone

        # URL de l'API
        self.url = reverse('send-otp')  # Assurez-vous que cette URL est correctement configurée dans vos URLs

    @patch('services.otp.OTPService.send_otp_by_sms')
    @patch('services.otp.OTPService.generate_otp')
    def test_send_otp_success(self, mock_generate_otp, mock_send_sms):
        # Mock de la génération de l'OTP
        mock_generate_otp.return_value = '123456'

        # Appel de l'API avec un numéro de téléphone valide
        data = {'phone_number': '1234567890'}
        response = self.client.post(self.url, data)

        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que la génération et l'envoi de l'OTP ont été appelés
        mock_generate_otp.assert_called_once_with(self.user, validity_duration=7200)
        mock_send_sms.assert_called_once_with('1234567890', '123456')

    def test_send_otp_user_not_found(self):
        # Appel de l'API avec un numéro de téléphone non existant
        data = {'phone_number': '0987654321'}
        response = self.client.post(self.url, data)

        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_otp_invalid_phone_number(self):
        # Appel de l'API avec des données invalides (par exemple, un numéro de téléphone mal formaté)
        data = {'phone_number': 'invalid_number'}
        response = self.client.post(self.url, data)

        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
