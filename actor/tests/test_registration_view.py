from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch
from actor.models import CustomUser, Wallet

class UserRegistrationViewTest(APITestCase):

    def setUp(self):
        self.url = reverse('user-registration')  # URL de la vue d'enregistrement
        self.valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '+1234567890'
        }

    @patch('services.otp.OTPService.generate_otp')
    @patch('services.otp.OTPService.send_otp_by_sms')
    def test_user_registration_success(self, mock_send_otp_by_sms, mock_generate_otp):
        """
        Teste la création réussie d'un utilisateur et l'envoi d'OTP.
        """
        # Configurer les mocks
        mock_generate_otp.return_value = '123456'  # OTP simulé
        mock_send_otp_by_sms.return_value = None   # Pas de retour attendu

        response = self.client.post(self.url, self.valid_data, format='json')

        # Vérifie que la réponse est un succès (201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifie la création de l'utilisateur dans la base de données
        user = CustomUser.objects.get(email=self.valid_data['email'])
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'john.doe@example.com')
        self.assertFalse(user.is_active)  # L'utilisateur doit être inactif par défaut

        # Vérifie la création du wallet pour l'utilisateur
        wallet = Wallet.objects.get(user=user)
        self.assertEqual(wallet.phone_number, self.valid_data['phone_number'])

        # Vérifie que les méthodes OTP ont été appelées correctement
        mock_generate_otp.assert_called_once_with(user)
        mock_send_otp_by_sms.assert_called_once_with(user, '123456')

    @patch('services.otp.OTPService.generate_otp')
    @patch('services.otp.OTPService.send_otp_by_sms')
    def test_user_registration_invalid_data(self, mock_send_otp_by_sms, mock_generate_otp):
        """
        Teste l'enregistrement avec des données invalides.
        """
        invalid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890'
        }

        response = self.client.post(self.url, invalid_data, format='json')

        # Vérifie que la réponse est un échec (400 Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Vérifie qu'aucun utilisateur n'a été créé
        self.assertEqual(CustomUser.objects.count(), 0)

        # Vérifie que les services OTP n'ont pas été appelés
        mock_generate_otp.assert_not_called()
        mock_send_otp_by_sms.assert_not_called()

    @patch('services.otp.OTPService.generate_otp')  # Remplacez par le chemin réel
    @patch('services.otp.OTPService.send_otp_by_sms')  # Remplacez par le chemin réel
    def test_duplicate_email(self, mock_send_otp_by_sms, mock_generate_otp):
        """
        Teste l'enregistrement avec un email déjà existant.
        """
        CustomUser.objects.create_user(
            username='1234567890',
            email='john.doe@example.com',
            first_name='John',
            last_name='Doe',
        )

        response = self.client.post(self.url, self.valid_data, format='json')

        # Vérifie que la réponse est une erreur (400 Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Vérifie qu'aucun utilisateur supplémentaire n'a été créé
        self.assertEqual(CustomUser.objects.count(), 1)

        # Vérifie que les services OTP n'ont pas été appelés
        mock_generate_otp.assert_not_called()
        mock_send_otp_by_sms.assert_not_called()

    @patch('services.otp.OTPService.generate_otp')  # Remplacez par le chemin réel
    @patch('services.otp.OTPService.send_otp_by_sms')  # Remplacez par le chemin réel
    def test_duplicate_phone_number(self, mock_send_otp_by_sms, mock_generate_otp):
        """
        Teste l'enregistrement avec un numéro de téléphone déjà existant.
        """
        CustomUser.objects.create_user(
            username='1234567890',
            email='existing@example.com',
            first_name='Jane',
            last_name='Doe',
        )

        invalid_data = self.valid_data.copy()
        invalid_data['phone_number'] = '1234567890'

        response = self.client.post(self.url, invalid_data, format='json')

        # Vérifie que la réponse est une erreur (400 Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Vérifie qu'aucun utilisateur supplémentaire n'a été créé
        self.assertEqual(CustomUser.objects.count(), 1)

        # Vérifie que les services OTP n'ont pas été appelés
        mock_generate_otp.assert_not_called()
        mock_send_otp_by_sms.assert_not_called()
