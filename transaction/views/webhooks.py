import hmac
import hashlib
import json
import logging
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction as db_transaction

from transaction.models import Transaction, TransactionStatus
from transaction.services.transaction import TransactionService

logger = logging.getLogger(__name__)


class DjamoWebhookView(APIView):
    """
    Endpoint pour recevoir les webhooks de Djamo
    
    Events supportés:
    - transactions/started: Transaction initiée
    - transactions/completed: Transaction réussie
    - transactions/failed: Transaction échouée
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # 1. Récupérer les headers et le payload
        signature = request.headers.get('x-djamo-hmac-sha256')
        topic = request.headers.get('x-djamo-webhook-topic')
        payload = request.body
        
        logger.info(f"Djamo webhook received - Topic: {topic}")
        
        # 2. Vérifier la signature HMAC
        if not self._verify_signature(payload, signature):
            logger.error("Invalid Djamo webhook signature")
            return Response(
                {"error": "Invalid signature"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 3. Parser le payload
        try:
            data = json.loads(payload)
            event_data = data.get('data', {})
            event_topic = data.get('topic', topic)
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload from Djamo")
            return Response(
                {"error": "Invalid JSON"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 4. Extraire les informations importantes
        reference = event_data.get('reference')  # Notre order_id
        djamo_status = event_data.get('status')  # completed, failed, started
        djamo_id = event_data.get('id')
        failure_reason = event_data.get('failureReason')
        
        logger.info(
            f"Processing Djamo webhook - Reference: {reference}, "
            f"Status: {djamo_status}, Topic: {event_topic}"
        )
        
        if not reference:
            logger.error("No reference in Djamo webhook payload")
            return Response(
                {"error": "Missing reference"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 5. Trouver la transaction
        try:
            transaction = Transaction.objects.get(order_id=reference)
        except Transaction.DoesNotExist:
            logger.error(f"Transaction not found for reference: {reference}")
            return Response(
                {"error": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 6. Mettre à jour la transaction selon l'événement
        with db_transaction.atomic():
            if event_topic == 'transactions/started':
                # Transaction démarrée (optionnel, déjà en PENDING)
                logger.info(f"Transaction {reference} started")
                
            elif event_topic == 'transactions/completed':
                # Transaction réussie
                self._handle_completed_transaction(
                    transaction, 
                    event_data,
                    djamo_id
                )
                
            elif event_topic == 'transactions/failed':
                # Transaction échouée
                self._handle_failed_transaction(
                    transaction,
                    failure_reason,
                    djamo_id
                )
            
            else:
                logger.warning(f"Unknown Djamo webhook topic: {event_topic}")
        
        # 7. Répondre avec un 200 pour confirmer la réception
        return Response(
            {"message": "Webhook received"},
            status=status.HTTP_200_OK
        )
    
    def _verify_signature(self, payload, signature):
        """
        Vérifie la signature HMAC du webhook Djamo
        """
        if not signature:
            logger.warning("No signature in Djamo webhook")
            return False
        
        secret_key = os.getenv('DJAMO_SECRET_KEY', '')
        
        if not secret_key:
            logger.error("DJAMO_SECRET_KEY not configured")
            return False
        
        # Calculer le HMAC
        computed_signature = hmac.new(
            secret_key.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Comparer les signatures
        return hmac.compare_digest(computed_signature, signature)
    
    def _handle_completed_transaction(self, transaction, event_data, djamo_id):
        """
        Gère une transaction complétée avec succès
        """
        logger.info(f"Completing transaction {transaction.order_id}")
        
        # Mettre à jour le statut
        TransactionService.update_transaction_status(
            transaction, 
            TransactionStatus.SUCCESS.value
        )
        
        # Ajouter l'ID externe Djamo
        if djamo_id:
            TransactionService.add_external_reference(transaction, djamo_id)
        
        # Ajouter les données supplémentaires
        TransactionService.add_additional_data(transaction, {
            'djamo_id': djamo_id,
            'djamo_status': event_data.get('status'),
            'fee': event_data.get('fee'),
            'totalAmount': event_data.get('totalAmount'),
            'completedAt': event_data.get('updatedAt')
        })
        
        # Créditer le wallet si c'est un TOPUP
        if transaction.transaction_type == 'TOPUP' and transaction.receiver:
            TransactionService.credit_wallet(
                transaction.receiver,
                transaction.amount,
                transaction,
                f"Recharge via Djamo - {djamo_id}"
            )
            
            # Appliquer les frais
            from transaction.services.fee import FeeService
            from transaction.models import TransactionType
            
            FeeService.apply_fee(
                user=transaction.receiver.user,
                wallet=transaction.receiver,
                transaction=transaction,
                transaction_type=TransactionType.TOPUP.value
            )
        
        logger.info(f"Transaction {transaction.order_id} completed successfully")
    
    def _handle_failed_transaction(self, transaction, failure_reason, djamo_id):
        """
        Gère une transaction échouée
        """
        logger.info(
            f"Failing transaction {transaction.order_id} - "
            f"Reason: {failure_reason}"
        )
        
        # Mettre à jour le statut
        TransactionService.update_transaction_status(
            transaction,
            TransactionStatus.FAILED.value
        )
        
        # Ajouter les informations d'échec
        TransactionService.add_additional_data(transaction, {
            'djamo_id': djamo_id,
            'failure_reason': failure_reason,
            'failed_at': None  # Timestamp actuel
        })
        
        logger.error(
            f"Transaction {transaction.order_id} failed - "
            f"Reason: {failure_reason}"
        )
