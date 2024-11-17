# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from actor.models import CustomUser
from services.otp import OTPService  # Assurez-vous que ce service OTP est correctement configuré
from actor.serializers import SendOTPSerializer

class SendOTPView(APIView):
    """
    Vue pour envoyer un OTP via SMS à l'utilisateur en fonction de son numéro de téléphone.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Sérialisation des données reçues
        serializer = SendOTPSerializer(data=request.data)

        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']

            # Vérifier si l'utilisateur existe
            try:
                user = CustomUser.objects.get(username=phone_number)
            except CustomUser.DoesNotExist:
                return Response({"error": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)

            # Générer l'OTP et l'envoyer par SMS
            otp = OTPService.generate_otp(user, validity_duration=7200)


            # Envoi de l'OTP par SMS (ici il faudrait utiliser un service comme Twilio ou Nexmo)
            OTPService.send_otp_by_sms(phone_number, otp)

            return Response(
                {"message": "OTP envoyé avec succès. Vérifiez votre SMS."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
