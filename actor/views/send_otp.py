# views.py
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from services.otp import (
    OTPService,
)
from actor.serializers import SendOTPSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class SendOTPView(APIView):
    """
    Vue pour envoyer un OTP via SMS à l'utilisateur en fonction de son numéro de téléphone.
    """

    permission_classes = [AllowAny]
    throttle_classes = ['services.throttling.AuthRateThrottle']

    @swagger_auto_schema(
        operation_description="Envoyer un code OTP par SMS pour vérification",
        request_body=SendOTPSerializer,
        responses={
            200: openapi.Response(
                description="OTP envoyé avec succès",
                examples={
                    "application/json": {
                        "message": "OTP envoyé avec succès. Vérifiez votre SMS - 123456"
                    }
                }
            ),
            400: openapi.Response(
                description="Numéro de téléphone invalide",
                examples={
                    "application/json": {
                        "phone_number": ["Ce champ est requis."]
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        # Sérialisation des données reçues
        serializer = SendOTPSerializer(data=request.data)

        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]

            # Générer l'OTP et l'envoyer par SMS
            otp = OTPService.generate_otp()

            # Vérifier si l'envoi d'OTP est activé
            otp_sending_enabled = os.getenv(
                "FF_OTP_SENDING_ENABLED", "True"
            ).lower() in ["true", "1"]

            if otp_sending_enabled:
                OTPService.send_otp_by_sms(phone_number, otp)

            return Response(
                {"message": f"OTP envoyé avec succès. Vérifiez votre SMS - {otp}"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
