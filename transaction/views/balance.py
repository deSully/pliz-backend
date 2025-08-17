from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from transaction.models import Wallet, WalletBalanceHistory
from transaction.serializers import WalletBalanceHistorySerializer


class BalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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
