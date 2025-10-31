# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from services.otp import OTPService
from actor.serializers import CheckOTPSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class CheckOTPView(APIView):
    """
    Vue pour connecter un utilisateur via son numéro de téléphone et un OTP.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Vérifier le code OTP reçu par SMS",
        request_body=CheckOTPSerializer,
        responses={
            200: openapi.Response(
                description="OTP valide",
                examples={
                    "application/json": {
                        "message": "OTP vérifié avec succès"
                    }
                }
            ),
            400: openapi.Response(
                description="OTP invalide ou expiré",
                examples={
                    "application/json": {
                        "error": "OTP invalide ou expiré."
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        # Sérialisation des données reçues
        serializer = CheckOTPSerializer(data=request.data)

        if serializer.is_valid():
            otp = serializer.validated_data["otp"]

            # Vérifier si l'OTP est valide
            if not OTPService.validate_otp(otp):
                return Response(
                    {"error": "OTP invalide ou expiré."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
