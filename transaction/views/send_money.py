from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from transaction.serializers import SendMoneySerializer
from drf_yasg.utils import swagger_auto_schema

import logging
logger = logging.getLogger(__name__)

class SendMoneyView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=SendMoneySerializer,  # Ajoute cette ligne
    )
    def post(self, request, *args, **kwargs):
        # On récupère l'utilisateur connecté via JWT
        sender = request.user

        # Ajout de l'utilisateur connecté dans les données du serializer
        data = request.data.copy()  # On copie les données pour y ajouter l'utilisateur connecté
        data['sender'] = sender.id

        # On crée une instance du serializer avec les nouvelles données
        try:
            logger.error(f"Data received for SendMoney: {data}")
            logger.error(f"User connected: {sender}")
            logger.error(request.data)

            serializer = SendMoneySerializer(data=data, context={"request": request})
            logger.info(f"Data received for SendMoney: {data}")
            logger.info(f"Serializer initialized with data: {serializer.initial_data}")

            if serializer.is_valid():
                serializer.save()  # Crée la transaction et met à jour les soldes
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Validation errors: {serializer.errors}")
                logger.error(f"Data received: {data}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in SendMoneyView: {str(e)}")
            # En cas d'erreur, on retourne les erreurs du serializer
            logger.error(f"Validation errors: {serializer.errors if serializer else 'No serializer'}")
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Si le serializer n'est pas valide, on retourne les erreurs
        logger.error(f"Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
