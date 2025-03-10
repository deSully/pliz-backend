# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from services.otp import OTPService
from actor.serializers import LoginSerializer
from actor.models import CustomUser
from services.token import TokenService
from django.contrib.auth import login
from drf_yasg.utils import swagger_auto_schema
from actor.serializers import LoginSerializer


class LoginView(APIView):
    """
    Vue pour connecter un utilisateur via son numéro de téléphone et un OTP.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,  # Ajoute cette ligne
    )
    def post(self, request, *args, **kwargs):
        # Sérialisation des données reçues
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            otp = serializer.validated_data["otp"]
            phone_number = serializer.validated_data["phone_number"]

            # Vérifier si l'OTP est valide
            if not OTPService.validate_otp(otp):
                return Response(
                    {"error": "OTP invalide ou expiré."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = CustomUser.objects.filter(username=phone_number).first()
            tokens = TokenService.generate_tokens_for_user(user)
            login(request, user)

            return Response(status=status.HTTP_200_OK, data=tokens)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
