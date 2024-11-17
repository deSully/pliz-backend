from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from actor.serializers import AccountActivationSerializer
from services.otp import OTPService  # Assurez-vous que ce chemin est correct

class UserAccountActivationView(APIView):
    """
    Vue pour activer un compte utilisateur via un OTP et un numéro de téléphone.
    """

    permission_classes = [AllowAny]  # N'importe qui peut tenter d'activer un compte

    def post(self, request, *args, **kwargs):
        # Sérialisation des données reçues
        serializer = AccountActivationSerializer(data=request.data)

        # Vérification si les données sont valides
        if serializer.is_valid():
            otp = serializer.validated_data['otp']

            # Récupérer l'utilisateur via le sérialiseur
            try:
                user = serializer.get_user()  # Utilisation de la méthode get_user() pour récupérer l'utilisateur
            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Vérifier l'OTP
            if not OTPService.validate_otp(user, otp):
                return Response(
                    {"error": "OTP invalide ou expiré."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Activer le compte
            user.is_active = True
            user.save()

            return Response(
                {"message": "Compte activé avec succès."},
                status=status.HTTP_200_OK
            )

        # Si les données sont invalides
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
