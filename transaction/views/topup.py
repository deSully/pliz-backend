from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from transaction.serializers import TopUpSerializer
from drf_yasg.utils import swagger_auto_schema

class TopUpView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=TopUpSerializer)
    def post(self, request, *args, **kwargs):
        user = request.user

        data = request.data.copy()
        data['sender'] = user.id

        serializer = TopUpSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            transaction = serializer.save()
            return Response({
                "message": "Compte rechargé avec succès.",
                "transaction_id": transaction.id,
                "amount": transaction.amount,
                "status": transaction.status,
                "timestamp": transaction.created_at
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
