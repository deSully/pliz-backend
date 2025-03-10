from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from transaction.serializers import SendMoneySerializer
from drf_yasg.utils import swagger_auto_schema

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
        serializer = SendMoneySerializer(data=data)

        if serializer.is_valid():
            serializer.save()  # Crée la transaction et met à jour les soldes
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
