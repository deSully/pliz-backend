from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from actor.serializers import UserRegistrationSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Créer un nouveau compte utilisateur",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Compte créé avec succès",
                examples={
                    "application/json": {
                        "message": "Compte créé avec succès"
                    }
                }
            ),
            400: openapi.Response(
                description="Données invalides",
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
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
