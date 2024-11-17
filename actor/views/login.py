# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from services.otp import OTPService
from actor.serializers import LoginWithOTPSerializer
from django.contrib.auth import login

from services.token import TokenService


class UserLoginView(APIView):
    """
    Vue pour connecter un utilisateur via son numéro de téléphone et un OTP.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Sérialisation des données reçues
        serializer = LoginWithOTPSerializer(data=request.data)

        if serializer.is_valid():
            otp = serializer.validated_data['otp']

            # Récupérer l'utilisateur via le numéro de téléphone
            user = serializer.get_user()

            # Vérifier si l'OTP est valide
            if not OTPService.validate_otp(user, otp):
                return Response({"error": "OTP invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)

            # Générer les tokens JWT
            tokens = TokenService.generate_tokens_for_user(user)
            login(request, user)

            return Response(
                {
                    "message": "Connexion réussie.",
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
