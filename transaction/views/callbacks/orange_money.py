from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # notifications publiques

from transaction.models import Transaction
from transaction.serializers import TopUpSerializer
from transaction.services.transaction import TransactionService

from drf_yasg.utils import swagger_auto_schema


class OrangeMoneyNotificationView(APIView):
    """
    Reçoit les notifications de paiement Orange Money et met à jour le compte Pliiz.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=TopUpSerializer)
    def post(self, request, *args, **kwargs):
        """
        Traite la notification de statut de paiement.
        """
        data = request.data
        order_id = data.get("order_id")
        payment_status = data.get("status")

        if not order_id or not payment_status:
            return Response(
                {"error": "order_id et status sont requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transaction = Transaction.objects.get(order_id=order_id)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction non trouvée"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment_status.upper() == "SUCCESS":
            TransactionService.credit_wallet(
                transaction.sender,
                transaction.amount,
                transaction,
                transaction.description,
            )

        TransactionService.update_transaction_status(transaction, payment_status)

        return Response(
            {"order_id": order_id, "status": payment_status}, status=status.HTTP_200_OK
        )
