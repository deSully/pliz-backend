from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from actor.models import CustomUser, Wallet

class UserRegistrationViewTest(APITestCase):

    def setUp(self):
        # Cette méthode est exécutée avant chaque test, pour configurer l'environnement de test.
        self.url = reverse('user-registration')  # Utilise l'URL de ta vue d'enregistrement d'utilisateur.
        self.valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '+1234567890'
        }

    def test_user_registration_success(self):
        """
        Test que l'enregistrement d'un utilisateur fonctionne correctement.
        """
        # On envoie une requête POST avec les données valides
        response = self.client.post(self.url, self.valid_data, format='json')

        # Vérification du statut de la réponse
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérification que l'utilisateur a bien été créé
        user = CustomUser.objects.get(email=self.valid_data['email'])
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'john.doe@example.com')

        # Vérifier que l'utilisateur est inactif par défaut
        self.assertFalse(user.is_active)

        # Vérification que le Wallet a bien été créé pour l'utilisateur
        wallet = Wallet.objects.get(user=user)
        self.assertEqual(wallet.phone_number, self.valid_data['phone_number'])

    def test_user_registration_invalid_data(self):
        """
        Test que l'API retourne une erreur lorsque les données sont invalides.
        """
        # Données invalides (email manquant)
        invalid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890'
        }

        response = self.client.post(self.url, invalid_data, format='json')

        # Vérification du statut de la réponse
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Vérification que l'utilisateur n'a pas été créé
        self.assertEqual(CustomUser.objects.count(), 0)
