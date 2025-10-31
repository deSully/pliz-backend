from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from actor.serializers import MerchantRegistrationSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class MerchantRegistrationView(APIView):
    """
    API pour l'inscription des marchands.
    
    Crée un compte utilisateur avec le type 'merchant', un wallet associé,
    et un profil marchand avec un code unique.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Créer un compte marchand avec code unique",
        request_body=MerchantRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Compte marchand créé avec succès",
                examples={
                    "application/json": {
                        "message": "Compte marchand créé avec succès",
                        "merchant_code": "MCH12345678",
                        "phone_number": "+221771234567"
                    }
                }
            ),
            400: openapi.Response(
                description="Données invalides ou téléphone déjà utilisé",
                examples={
                    "application/json": {
                        "detail": "Ce numéro de téléphone est déjà utilisé.",
                        "code": "PHONE_EXISTS"
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = MerchantRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            merchant = user.wallet.merchant_wallet
            
            return Response(
                {
                    "message": "Compte marchand créé avec succès",
                    "merchant_code": merchant.merchant_code,
                    "phone_number": user.username
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
