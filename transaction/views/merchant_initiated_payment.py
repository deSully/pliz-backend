from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from actor.models import Wallet, Merchant
from transaction.serializers_merchant import MerchantInitiatedPaymentSerializer
from transaction.services.transaction import TransactionService
from transaction.services.fee import FeeService
from transaction.models import TransactionType, TransactionStatus
from services.throttling import TransactionRateThrottle
from services.mqtt import mqtt_service

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction as db_transaction

import logging

logger = logging.getLogger(__name__)


class MerchantInitiatedPaymentView(APIView):
    """
    API pour les paiements initiés par un marchand.
    
    Flow:
    1. Le marchand scanne le QR code du client
    2. Le marchand envoie le numéro de téléphone du client + montant
    3. Le système débite le client et crédite le marchand directement
    
    Cette API nécessite que l'utilisateur connecté soit un marchand.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [TransactionRateThrottle]

    @swagger_auto_schema(
        operation_description="[MARCHAND UNIQUEMENT] Initier un paiement après avoir scanné le QR code du client",
        request_body=MerchantInitiatedPaymentSerializer,
        responses={
            200: openapi.Response(
                description="Paiement effectué avec succès",
                examples={
                    "application/json": {
                        "message": "Paiement effectué avec succès",
                        "transaction": {
                            "order_id": "PAY-20251031-XYZ123",
                            "amount": 3500.00,
                            "customer_phone": "+221771234567",
                            "merchant_name": "Boutique Diallo",
                            "description": "Paiement chez Boutique Diallo - Achat produits",
                            "status": "SUCCESS",
                            "timestamp": "2025-10-31T15:45:00Z"
                        }
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
            403: openapi.Response(
                description="Utilisateur non autorisé",
                examples={
                    "application/json": {
                        "detail": "Seuls les marchands peuvent initier des paiements.",
                        "code": "UNAUTHORIZED_USER_TYPE"
                    }
                }
            ),
            404: openapi.Response(
                description="Client ou wallet non trouvé",
                examples={
                    "application/json": {
                        "detail": "Ce numéro de téléphone n'existe pas ou n'est pas actif.",
                        "code": "CUSTOMER_NOT_FOUND"
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Vérifier que l'utilisateur connecté est un marchand
        if user.user_type != "merchant":
            return Response(
                {
                    "detail": "Seuls les marchands peuvent initier des paiements.",
                    "code": "UNAUTHORIZED_USER_TYPE"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MerchantInitiatedPaymentSerializer(data=request.data)
        
        if serializer.is_valid():
            customer_wallet = serializer.validated_data["customer_wallet"]
            amount = serializer.validated_data["amount"]
            description = serializer.validated_data.get(
                "description", 
                "Paiement marchand"
            )
            
            try:
                # Récupérer le wallet et le profil marchand
                merchant_wallet = Wallet.objects.get(user=user)
                merchant = Merchant.objects.get(wallet=merchant_wallet)
                
                # Enrichir la description
                full_description = f"Paiement chez {merchant.business_name} - {description}"
                
                # Traiter le paiement dans une transaction atomique
                with db_transaction.atomic():
                    # Vérifier les fonds du client
                    TransactionService.check_sufficient_funds(customer_wallet, amount)
                    
                    # Créer la transaction
                    transaction = TransactionService.create_pending_transaction(
                        sender_wallet=customer_wallet,
                        receiver_wallet=merchant_wallet,
                        transaction_type=TransactionType.PAYMENT.value,
                        amount=amount,
                        description=full_description
                    )
                    
                    logger.info(
                        f"Merchant-initiated payment created: {transaction.order_id} "
                        f"from {customer_wallet.phone_number} to {merchant.merchant_code}"
                    )
                    
                    # Débiter le client
                    TransactionService.debit_wallet(
                        customer_wallet, 
                        amount, 
                        transaction, 
                        full_description
                    )
                    
                    # Créditer le marchand
                    TransactionService.credit_wallet(
                        merchant_wallet, 
                        amount, 
                        transaction, 
                        full_description
                    )
                    
                    # Mettre à jour le statut en SUCCESS
                    TransactionService.update_transaction_status(
                        transaction, 
                        TransactionStatus.SUCCESS.value
                    )
                    
                    # Appliquer les frais après confirmation du succès
                    FeeService.apply_fee(
                        user=customer_wallet.user,
                        wallet=customer_wallet,
                        transaction=transaction,
                        transaction_type=TransactionType.PAYMENT.value,
                        merchant=merchant
                    )
                    
                    # Notifications MQTT supplémentaires pour scan & pay
                    if hasattr(customer_wallet.user, 'uuid'):
                        mqtt_service.publish_transaction_notification(
                            user_uuid=str(customer_wallet.user.uuid),
                            action="payment",
                            status="success",
                            title="🏪 Paiement effectué",
                            message=f"Paiement de {amount} FCFA chez {merchant.business_name}",
                            transaction_data={
                                "transaction_id": transaction.order_id,
                                "amount": float(amount),
                                "merchant": merchant.business_name
                            }
                        )
                    
                    return Response(
                        {
                            "message": "Paiement effectué avec succès",
                            "transaction": {
                                "order_id": transaction.order_id,
                                "amount": float(transaction.amount),
                                "customer_phone": customer_wallet.phone_number,
                                "merchant_name": merchant.business_name,
                                "description": full_description,
                                "status": transaction.status,
                                "timestamp": transaction.timestamp
                            }
                        },
                        status=status.HTTP_200_OK
                    )
                    
            except Wallet.DoesNotExist:
                return Response(
                    {
                        "detail": "Le portefeuille du marchand n'existe pas.",
                        "code": "MERCHANT_WALLET_NOT_FOUND"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            except Merchant.DoesNotExist:
                return Response(
                    {
                        "detail": "Le profil marchand n'existe pas.",
                        "code": "MERCHANT_PROFILE_NOT_FOUND"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError as e:
                logger.error(f"Insufficient funds error: {str(e)}")
                return Response(
                    {
                        "detail": str(e),
                        "code": "INSUFFICIENT_FUNDS"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Unexpected error in merchant payment: {str(e)}")
                return Response(
                    {
                        "detail": f"Une erreur est survenue lors du traitement du paiement: {str(e)}",
                        "code": "PAYMENT_PROCESSING_ERROR"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Erreurs de validation
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
