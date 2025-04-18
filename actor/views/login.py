# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from actor.serializers import LoginSerializer
from actor.models import CustomUser
from services.token import TokenService
from django.contrib.auth import login
from drf_yasg.utils import swagger_auto_schema

from utils.dejavu import deja_vu

class LoginView(APIView):
    """
    Vue pour connecter un utilisateur via son numéro de téléphone et un OTP.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,  # Ajoute cette ligne
    )
    @deja_vu
    def post(self, request, *args, **kwargs):
        # Sérialisation des données reçues
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            pin = serializer.validated_data["pin"]
            phone_number = serializer.validated_data["phone_number"]

            user = CustomUser.objects.filter(username=phone_number).first()
            test_a_fuction()
            if not user.check_password(pin):
                return Response(
                    {"error": "Le code PIN est incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            tokens = TokenService.generate_tokens_for_user(user)
            login(request, user)

            return Response(status=status.HTTP_200_OK, data=tokens)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def test_a_fuction():
    """
    Test de la fonction test_a_fuction.
    """
    pass
    return 'test_a_fuction'