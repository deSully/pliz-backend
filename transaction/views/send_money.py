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

    @swagger_auto_schema(request_body=SendMoneySerializer)
    def post(self, request, *args, **kwargs):
        data = request.data.copy()

        try:
            logger.info(f"Data received for SendMoney: {data}")

            serializer = SendMoneySerializer(data=data, context={"request": request})
            if serializer.is_valid():
                transaction = serializer.save()
                logger.info(f"Transaction created: {transaction}")
                order_id = transaction.order_id
                amount = transaction.amount

                # Récupérer le wallet de l’utilisateur connecté
                wallet = (
                    transaction.sender
                )  # adapte selon ton modèle (sender -> wallet)
                new_balance = (
                    wallet.wallet_balance_histories.order_by("-timestamp")
                    .first()
                    .balance_after
                )

                return Response(
                    {
                        "reference": order_id,
                        "amount": str(amount),
                        "balance_after_operation": str(new_balance),
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                # On renvoie seulement le premier message d'erreur avec code
                field, messages = next(iter(serializer.errors.items()))
                response_data = {
                    "detail": messages[0],
                    "code": field.upper() + "_ERROR",
                }
                logger.error(f"Validation error: {response_data}")
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in SendMoneyView: {str(e)}")
            return Response(
                {"detail": str(e), "code": "TRANSACTION_FAILED"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
