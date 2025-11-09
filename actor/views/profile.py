from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from actor.serializers import UserProfileSerializer
from actor.models import Merchant


class UserProfileView(APIView):
    """
    GET: Récupérer les informations du profil utilisateur
    PUT: Mettre à jour les informations du profil
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupérer les informations complètes du profil utilisateur connecté",
        responses={
            200: openapi.Response(
                description="Informations du profil",
                examples={
                    "application/json": {
                        "id": 1,
                        "uuid": "550e8400-e29b-41d4-a716-446655440000",
                        "username": "+221771234567",
                        "phone_number": "+221771234567",
                        "first_name": "Mamadou",
                        "last_name": "Diallo",
                        "email": "mamadou@example.com",
                        "user_type": "merchant",
                        "is_subscribed": False,
                        "wallet": {
                            "id": 42,
                            "phone_number": "+221771234567",
                            "currency": "XOF",
                            "balance": 125000.00,
                            "is_platform": False
                        },
                        "merchant": {
                            "merchant_code": "MCH12345678",
                            "business_name": "Boutique Diallo",
                            "address": "Dakar, Senegal"
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Mettre à jour les informations du profil (nom, prénom, infos marchand)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Prénom'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom de famille'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                'business_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du commerce (marchand uniquement)'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='Adresse (marchand uniquement)'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Profil mis à jour avec succès",
                examples={
                    "application/json": {
                        "message": "Profil mis à jour avec succès",
                        "profile": {
                            "first_name": "Mamadou",
                            "last_name": "Diallo",
                            "email": "mamadou@example.com",
                            "business_name": "Boutique Diallo & Fils"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Données invalides",
                examples={
                    "application/json": {
                        "detail": "Champ invalide",
                        "code": "VALIDATION_ERROR"
                    }
                }
            )
        }
    )
    def put(self, request):
        """Mettre à jour le profil de l'utilisateur connecté"""
        user = request.user
        data = request.data

        # Champs autorisés pour tous les utilisateurs
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']

        user.save()

        # Si c'est un marchand, mettre à jour les infos spécifiques
        if user.user_type == "merchant":
            try:
                merchant = Merchant.objects.get(wallet__user=user)
                if 'business_name' in data:
                    merchant.business_name = data['business_name']
                if 'address' in data:
                    merchant.address = data['address']
                merchant.save()
            except Merchant.DoesNotExist:
                return Response(
                    {
                        "detail": "Profil marchand non trouvé",
                        "code": "MERCHANT_NOT_FOUND"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        # Retourner le profil mis à jour
        serializer = UserProfileSerializer(user)
        return Response(
            {
                "message": "Profil mis à jour avec succès",
                "profile": serializer.data
            },
            status=status.HTTP_200_OK
        )
