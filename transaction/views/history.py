from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from actor.models import Wallet
from transaction.models import Transaction
from transaction.serializers import TransactionSerializer


class TransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (format: Bearer <token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get_queryset(self):
        user = self.request.user
        wallet = Wallet.objects.get(user=user)
        transactions = Transaction.objects.filter(sender=wallet) | Transaction.objects.filter(receiver=wallet)
        return transactions.order_by('-timestamp')
