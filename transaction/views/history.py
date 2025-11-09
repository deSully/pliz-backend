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
        operation_description="Récupérer l'historique complet des transactions de l'utilisateur (envoyées et reçues)",
        responses={
            200: openapi.Response(
                description="Liste des transactions",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "order_id": "TRF-20251109-ABC123",
                            "transaction_type": "TRANSFER",
                            "amount": 5000.00,
                            "sender": {
                                "wallet_id": 42,
                                "phone_number": "+221771234567",
                                "user_id": 2,
                                "name": "Mamadou Diallo"
                            },
                            "receiver": {
                                "wallet_id": 87,
                                "phone_number": "+221779876543",
                                "user_id": 5,
                                "name": "Fatou Sow",
                                "merchant_code": "MCHEC00D910",
                                "business_name": "Boutique Fatou"
                            },
                            "timestamp": "2025-10-31T14:30:00Z",
                            "description": "Transfert à Fatou",
                            "status": "SUCCESS",
                            "balance_histories": [
                                {
                                    "balance_before": 50000.00,
                                    "balance_after": 45000.00,
                                    "transaction_type": "DEBIT",
                                    "timestamp": "2025-10-31T14:30:00Z",
                                    "description": "Transfert à Fatou"
                                }
                            ]
                        }
                    ]
                }
            )
        }
    )
    def get_queryset(self):
        user = self.request.user
        wallet = Wallet.objects.get(user=user)
        
        # Utiliser Q objects pour une requête unique et sécurisée
        from django.db.models import Q
        transactions = Transaction.objects.filter(
            Q(sender=wallet) | Q(receiver=wallet)
        ).distinct()
        
        return transactions.order_by('-timestamp')
