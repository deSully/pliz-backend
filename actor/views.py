from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer
from services import OTPService  # Le service OTP importé ici

class UserRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        # Valider et créer l'utilisateur
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            # Sauvegarder l'utilisateur
            user = serializer.save()

            # Marquer le compte comme inactif par défaut
            user.is_active = False
            user.save()

            # Générer l'OTP pour l'utilisateur
            otp = OTPService.generate_otp(user)

            # Envoi de l'OTP par SMS ou email
            OTPService.send_otp_by_sms(user, otp)  # Envoi par SMS avec Twilio
            # ou OTPService.send_otp_by_email(user, otp)  # Envoi par email si nécessaire

            return Response({
                "message": "Utilisateur créé. Un code OTP a été envoyé par SMS pour valider votre compte."
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
