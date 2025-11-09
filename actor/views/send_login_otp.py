# views.py
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from actor.models import CustomUser
from services.otp import (
    OTPService,
)
from actor.serializers import SendOTPSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import logging

logger = logging.getLogger(__name__)

class SendLoginOTPView(APIView):
    """
    Vue pour envoyer un OTP via SMS à l'utilisateur en fonction de son numéro de téléphone.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=SendOTPSerializer,  # Ajoute cette ligne
        responses={200: openapi.Response("OTP envoyé avec succès")},
    )
    def post(self, request, *args, **kwargs):
        # Sérialisation des données reçues
        serializer = SendOTPSerializer(data=request.data)

        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]

            customer = CustomUser.objects.filter(username=phone_number).first()
            if not customer:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Générer l'OTP et l'envoyer par SMS
            otp = OTPService.generate_otp()
            logger.info(f"OTP généré pour {phone_number}")

            # Vérifier si l'envoi d'OTP est activé
            otp_sending_enabled = os.getenv(
                "FF_OTP_SENDING_ENABLED", "True"
            ).lower() in ["true", "1"]

            if otp_sending_enabled:
                OTPService.send_otp_by_sms(phone_number, otp)
                return Response(
                    {"message": "OTP envoyé avec succès. Vérifiez votre SMS"},
                    status=status.HTTP_200_OK,
                )
            else:
                # Mode dev/test : retourner l'OTP dans la réponse (SMS désactivé)
                return Response(
                    {"message": f"Mode test - OTP: {otp} (SMS non envoyé)"},
                    status=status.HTTP_200_OK,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
