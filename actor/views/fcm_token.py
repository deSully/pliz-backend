from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import logging

logger = logging.getLogger(__name__)


class RegisterFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Enregistrer ou mettre à jour le token FCM de l'appareil pour les notifications push",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["token"],
            properties={
                "token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Token FCM de l'appareil (Firebase Cloud Messaging)",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Token enregistré avec succès",
                examples={"application/json": {"detail": "Token FCM enregistré avec succès."}},
            ),
            400: openapi.Response(description="Token manquant"),
        },
    )
    def post(self, request, *args, **kwargs):
        token = request.data.get("token", "").strip()

        if not token:
            return Response(
                {"detail": "Le token FCM est requis.", "code": "MISSING_TOKEN"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.fcm_token = token
        request.user.save(update_fields=["fcm_token"])

        logger.info(f"FCM token updated for user {request.user.username}")

        return Response(
            {"detail": "Token FCM enregistré avec succès."},
            status=status.HTTP_200_OK,
        )
