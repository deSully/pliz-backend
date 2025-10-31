from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from transaction.models import Wallet, WalletBalanceHistory
from transaction.serializers import WalletBalanceHistorySerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class BalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Récupérer le solde actuel du portefeuille de l'utilisateur",
        responses={
            200: openapi.Response(
                description="Solde du portefeuille",
                examples={
                    "application/json": {
                        "current_balance": 50000.00,
                        "currency": "XOF",
                        "last_transaction": {
                            "balance_before": 45000.00,
                            "balance_after": 50000.00,
                            "transaction_type": "TOPUP",
                            "timestamp": "2025-10-31T10:30:00Z",
                            "description": "Rechargement VIA WAVE"
                        }
                    }
                }
            ),
            404: "Aucun portefeuille associé à cet utilisateur"
        }
    )
    def get(self, request):
        user = request.user

        try:
            wallet = Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            return Response(
                {"detail": "Aucun portefeuille associé à cet utilisateur."},
                status=status.HTTP_404_NOT_FOUND,
            )

        latest_history = (
            WalletBalanceHistory.objects.filter(wallet=wallet)
            .order_by("-timestamp")
            .first()
        )
        history_data = (
            WalletBalanceHistorySerializer(latest_history).data
            if latest_history
            else None
        )

        return Response(
            {
                "current_balance": latest_history.balance_after if latest_history else 0,
                "currency": wallet.currency,
                "last_transaction": history_data,
            },
            status=status.HTTP_200_OK,
        )
