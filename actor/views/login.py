# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from actor.serializers import LoginSerializer
from actor.models import CustomUser
from services.token import TokenService
from services.throttling import AuthRateThrottle
from django.contrib.auth import login
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """
    Vue pour connecter un utilisateur via son numéro de téléphone et un code PIN.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @swagger_auto_schema(
        operation_description="Connexion avec numéro de téléphone et code PIN",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Connexion réussie - JWT tokens et infos utilisateur",
                examples={
                    "application/json": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "uuid": "550e8400-e29b-41d4-a716-446655440000",
                        "user_type": "merchant",
                        "phone_number": "+221771234567",
                        "first_name": "Mamadou",
                        "last_name": "Diallo",
                        "merchant": {
                            "merchant_code": "MCH12345678",
                            "business_name": "Boutique Diallo",
                            "address": "Dakar, Senegal"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Code PIN incorrect",
                examples={
                    "application/json": {
                        "error": "Le code PIN est incorrect."
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        # Sérialisation des données reçues
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            pin = serializer.validated_data["pin"]
            phone_number = serializer.validated_data["phone_number"]

            user = CustomUser.objects.filter(username=phone_number).first()
            if not user:
                logger.warning(f"LOGIN_FAILED: User not found for phone {phone_number}")
                return Response(
                    {"error": "Utilisateur non trouvé."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            if not user.check_password(pin):
                logger.warning(f"LOGIN_FAILED: Incorrect PIN for user {phone_number}")
                return Response(
                    {"error": "Le code PIN est incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            tokens = TokenService.generate_tokens_for_user(user)
            login(request, user)
            logger.info(f"LOGIN_SUCCESS: User {phone_number} ({user.user_type}) logged in successfully")

            # Préparer la réponse avec les infos utilisateur
            response_data = {
                **tokens,
                "uuid": str(user.uuid),
                "user_type": user.user_type,
                "phone_number": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            }

            # Si c'est un marchand, ajouter les infos spécifiques
            if user.user_type == "merchant":
                try:
                    merchant = user.wallet.merchant_wallet
                    response_data["merchant"] = {
                        "merchant_code": merchant.merchant_code,
                        "business_name": merchant.business_name,
                        "address": merchant.address
                    }
                except Exception:
                    pass  # Si le profil marchand n'existe pas encore

            return Response(status=status.HTTP_200_OK, data=response_data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



