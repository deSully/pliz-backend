from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from transaction.models import Transaction, FeeDistribution, WalletBalanceHistory


class TransactionDetailView(APIView):
    """
    Récupérer le détail complet d'une transaction par son order_id
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupérer tous les détails d'une transaction (montant, frais, distributions, historique wallet)",
        manual_parameters=[
            openapi.Parameter(
                'order_id',
                openapi.IN_PATH,
                description="Order ID de la transaction",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Détails complets de la transaction",
                examples={
                    "application/json": {
                        "order_id": "TRF-20251031-ABC123",
                        "transaction_type": "TRANSFER",
                        "amount": 5000.00,
                        "fee_applied": 50.00,
                        "status": "SUCCESS",
                        "timestamp": "2025-10-31T14:30:00Z",
                        "description": "Transfert à Fatou",
                        "sender": {
                            "phone_number": "+221771234567",
                            "name": "Mamadou Diallo"
                        },
                        "receiver": {
                            "phone_number": "+221779876543",
                            "name": "Fatou Sow"
                        },
                        "fee_distributions": [
                            {
                                "actor_type": "PROVIDER",
                                "actor_id": None,
                                "amount": 25.00
                            },
                            {
                                "actor_type": "BANK",
                                "actor_id": None,
                                "amount": 25.00
                            }
                        ],
                        "balance_histories": [
                            {
                                "wallet_owner": "+221771234567",
                                "balance_before": 50000.00,
                                "balance_after": 44950.00,
                                "transaction_type": "DEBIT",
                                "description": "Transfert à Fatou"
                            }
                        ],
                        "additional_data": {}
                    }
                }
            ),
            403: openapi.Response(
                description="Vous ne pouvez pas voir cette transaction",
                examples={
                    "application/json": {
                        "detail": "Vous n'êtes pas autorisé à voir cette transaction.",
                        "code": "FORBIDDEN"
                    }
                }
            ),
            404: openapi.Response(
                description="Transaction non trouvée",
                examples={
                    "application/json": {
                        "detail": "Transaction non trouvée.",
                        "code": "TRANSACTION_NOT_FOUND"
                    }
                }
            )
        }
    )
    def get(self, request, order_id):
        """Récupérer le détail d'une transaction"""
        user = request.user
        
        try:
            transaction = Transaction.objects.get(order_id=order_id)
        except Transaction.DoesNotExist:
            return Response(
                {
                    "detail": "Transaction non trouvée.",
                    "code": "TRANSACTION_NOT_FOUND"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier que l'utilisateur a le droit de voir cette transaction
        user_wallet = user.wallet
        if transaction.sender != user_wallet and transaction.receiver != user_wallet:
            return Response(
                {
                    "detail": "Vous n'êtes pas autorisé à voir cette transaction.",
                    "code": "FORBIDDEN"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer les distributions de frais
        fee_distributions = FeeDistribution.objects.filter(transaction=transaction)
        fee_distributions_data = [
            {
                "actor_type": dist.actor_type,
                "actor_id": dist.actor_id,
                "amount": float(dist.amount)
            }
            for dist in fee_distributions
        ]
        
        # Récupérer l'historique des wallets liés à cette transaction
        balance_histories = WalletBalanceHistory.objects.filter(transaction=transaction)
        balance_histories_data = [
            {
                "wallet_owner": history.wallet.phone_number,
                "balance_before": float(history.balance_before),
                "balance_after": float(history.balance_after),
                "transaction_type": history.transaction_type,
                "timestamp": history.timestamp,
                "description": history.description
            }
            for history in balance_histories
        ]
        
        # Construire la réponse
        response_data = {
            "order_id": transaction.order_id,
            "transaction_type": transaction.transaction_type,
            "amount": float(transaction.amount),
            "fee_applied": float(transaction.fee_applied) if transaction.fee_applied else 0.00,
            "status": transaction.status,
            "timestamp": transaction.timestamp,
            "description": transaction.description or "",
            "sender": {
                "phone_number": transaction.sender.phone_number if transaction.sender else None,
                "name": f"{transaction.sender.user.first_name} {transaction.sender.user.last_name}" if transaction.sender else None
            } if transaction.sender else None,
            "receiver": {
                "phone_number": transaction.receiver.phone_number if transaction.receiver else None,
                "name": f"{transaction.receiver.user.first_name} {transaction.receiver.user.last_name}" if transaction.receiver else None
            } if transaction.receiver else None,
            "fee_distributions": fee_distributions_data,
            "balance_histories": balance_histories_data,
            "additional_data": transaction.additional_data or {}
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
