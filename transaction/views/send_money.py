from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from transaction.serializers import SendMoneySerializer
from services.throttling import TransactionRateThrottle
from services.firebase import firebase_service
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import logging

logger = logging.getLogger(__name__)


class SendMoneyView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [TransactionRateThrottle]

    @swagger_auto_schema(
        operation_description="Envoyer de l'argent - Transfert interne ou via partenaire (Wave, Orange Money, MTN)",
        request_body=SendMoneySerializer,
        responses={
            201: openapi.Response(
                description="Transfert effectué avec succès",
                examples={
                    "application/json": {
                        "reference": "TRF-20251031-ABC123",
                        "amount": "5000.00",
                        "balance_after_operation": "45000.00"
                    }
                }
            ),
            400: openapi.Response(
                description="Fonds insuffisants ou données invalides",
                examples={
                    "application/json": {
                        "detail": "Le solde est insuffisant pour effectuer cette transaction.",
                        "code": "INSUFFICIENT_FUNDS"
                    }
                }
            ),
            500: openapi.Response(
                description="Erreur lors du traitement",
                examples={
                    "application/json": {
                        "detail": "Le traitement du transfer a échoué.",
                        "code": "PAYMENT_PROCESSING_ERROR"
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        data = request.data.copy()

        try:
            logging.info(f"Received data for SendMoneyView: {data}")

            serializer = SendMoneySerializer(data=data, context={"request": request})
            if serializer.is_valid():
                transaction = serializer.save()
                logging.info(f"Transaction created: {transaction}")

                order_id = transaction.order_id
                amount = transaction.amount

                wallet = (
                    transaction.sender
                )
                new_balance = (
                    wallet.wallet_balance_histories.order_by("-timestamp")
                    .first()
                    .balance_after
                )

                logger.info(
                    f"Transaction successful: {order_id}, Amount: {amount}, New Balance: {new_balance}"
                )
                
                # Notification FCM - sender
                firebase_service.send_transaction_notification(
                    fcm_token=getattr(request.user, "fcm_token", None),
                    action="send_money",
                    status="success",
                    title="Envoi en cours",
                    message=f"Votre envoi de {amount} FCFA est en cours de traitement",
                    transaction_data={
                        "transaction_id": order_id,
                        "amount": float(amount),
                        "receiver": transaction.receiver.phone_number if transaction.receiver else "N/A",
                    },
                )
                # Notification FCM - receiver (argent reçu)
                if transaction.receiver and transaction.receiver.user:
                    firebase_service.send_transaction_notification(
                        fcm_token=getattr(transaction.receiver.user, "fcm_token", None),
                        action="receive_money",
                        status="success",
                        title="Argent reçu",
                        message=f"Vous avez reçu {amount} FCFA",
                        transaction_data={
                            "transaction_id": order_id,
                            "amount": float(amount),
                            "sender": transaction.sender.phone_number if transaction.sender else "N/A",
                        },
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
                field, messages = next(iter(serializer.errors.items()))
                response_data = {
                    "detail": messages[0],
                    "code": field.upper() if field else "VALIDATION_ERROR",
                }
                logger.error(f"Validation error: {response_data}")
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in SendMoneyView: {str(e)}")
            return Response(
                {"detail": str(e), "code": "TRANSACTION_FAILED"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
