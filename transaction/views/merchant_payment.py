from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from actor.models import Wallet, Merchant
from transaction.errors import PaymentProcessingError
from transaction.serializers import MerchantPaymentSerializer
from transaction.merchants.service import MerchantPaymentService
from services.throttling import TransactionRateThrottle
from services.mqtt import mqtt_service

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import logging

logger = logging.getLogger(__name__)


class MerchantPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [TransactionRateThrottle]

    @swagger_auto_schema(
        operation_description="Payer un marchand (Woyofal, Rapido, Airtime, etc.) via leur API spécifique",
        request_body=MerchantPaymentSerializer,
        responses={
            200: openapi.Response(
                description="Paiement marchand effectué avec succès",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "order_id": "PAY-20251031-ABC123",
                            "amount": 2500.00,
                            "merchant_code": "WOYOFAL"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Fonds insuffisants ou champs manquants",
                examples={
                    "application/json": {
                        "detail": "Le solde est insuffisant pour effectuer cette transaction.",
                        "code": "INSUFFICIENT_FUNDS"
                    }
                }
            ),
            404: openapi.Response(
                description="Marchand non trouvé",
                examples={
                    "application/json": {
                        "detail": "Le marchand spécifié n'existe pas.",
                        "code": "MERCHANT_NOT_FOUND"
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        sender = request.user
        serializer = MerchantPaymentSerializer(data=request.data)

        if serializer.is_valid():
            merchant_code = serializer.validated_data["merchant_code"]
            amount = serializer.validated_data["amount"]
            details = serializer.validated_data["details"]

            try:
                sender_wallet = Wallet.objects.get(user=sender)
                merchant = Merchant.objects.get(merchant_code=merchant_code)

                response = MerchantPaymentService.process_payment(
                    merchant, sender_wallet, amount, details
                )
                
                # Notification MQTT pour paiement API marchand
                if hasattr(sender, 'uuid'):
                    mqtt_service.publish_transaction_notification(
                        user_uuid=str(sender.uuid),
                        action="payment",
                        status="success",
                        title="🏪 Paiement marchand",
                        message=f"Paiement de {amount} FCFA via {merchant_code}",
                        transaction_data={
                            "merchant_code": merchant_code,
                            "amount": float(amount),
                            "details": details
                        }
                    )

                return Response(response, status=status.HTTP_200_OK)

            except ValueError as e:
                return Response(
                    {"detail": str(e), "code": "VALUE_ERROR"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Merchant.DoesNotExist:
                return Response(
                    {
                        "detail": "Le marchand spécifié n'existe pas.",
                        "code": "MERCHANT_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Wallet.DoesNotExist:
                return Response(
                    {
                        "detail": "Le portefeuille de l'envoyeur n'existe pas.",
                        "code": "WALLET_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            except PaymentProcessingError as e:
                logger.error(f"Payment processing error: {str(e)}")
                return Response(
                    {"detail": str(e), "code": "PAYMENT_PROCESSING_ERROR"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            except Exception as e:
                logger.error(f"Unexpected error in merchant payment: {str(e)}")
                return Response(
                    {
                        "detail": f"Une erreur inattendue est survenue: {str(e)}",
                        "code": "INTERNAL_SERVER_ERROR",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Renvoie les erreurs du serializer avec détail et code
        field, messages = next(iter(serializer.errors.items()))
        return Response(
            {"detail": messages[0], "code": field.upper() + "_ERROR"},
            status=status.HTTP_400_BAD_REQUEST,
        )
