from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ToggleSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Activer/désactiver l'abonnement de l'utilisateur",
        responses={
            200: openapi.Response(
                description="Abonnement mis à jour avec succès",
                examples={
                    "application/json": {
                        "message": "Abonnement mis à jour avec succès.",
                        "is_subscribed": True
                    }
                }
            )
        }
    )
    def post(self, request):
        user = request.user
        user.is_subscribed = not user.is_subscribed
        user.save()
        return Response({
            "message": "Abonnement mis à jour avec succès.",
            "is_subscribed": user.is_subscribed
        }, status=status.HTTP_200_OK)
