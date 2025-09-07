from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from .models import Transaction, WalletBalanceHistory, TransactionType, TransactionStatus
from actor.models import Wallet
from actor.merchant_policy import MERCHANT_POLICIES
from transaction.services.transaction import TransactionService

from transaction.errors import PaymentProcessingError

from transaction.partners.factory import PartnerGatewayFactory

import logging

logger = logging.getLogger(__name__)


class SendMoneySerializer(serializers.ModelSerializer):
    receiver = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    partner = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Transaction
        fields = ["receiver", "amount"]
        read_only_fields = ["status"]

    def validate(self, data):
        logging.info(f"Validating data: {data}")

        if data["amount"] <= 0:
            raise serializers.ValidationError(
                detail="Le montant doit être positif.", code="INVALID_AMOUNT"
            )

        try:    
            logging.info(f"Validating data: {data}")

            sender_wallet = Wallet.objects.get(user=self.context["request"].user)

            if not sender_wallet.user.is_active:
                raise serializers.ValidationError(
                    detail="L'utilisateur envoyeur est inactif.",
                    code="SENDER_INACTIVE_ERROR",
                )
            logger.info(f"Checking sufficient funds for {sender_wallet.user.username}")
            TransactionService.check_sufficient_funds(sender_wallet, data["amount"])

        except Wallet.DoesNotExist:
            raise serializers.ValidationError(
                detail="Un des portefeuilles spécifiés n'existe pas.",
                code="WALLET_NOT_FOUND_ERROR",
            )
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "code": "WALLET_NOT_FOUND_ERROR",
                    "message": "Un des portefeuilles spécifiés n'existe pas.",
                }
            )
        except serializers.ValidationError as e:
            raise e

        return data

    def create(self, validated_data):
        logger.info(f"Creating transaction with data: {self.context["request"].user}")

        sender_wallet = Wallet.objects.get(user__username=self.context["request"].user)

        if "partner" not in validated_data:
            # Si pas de partenaire, c'est un transfert interne
            receiver_wallet = Wallet.objects.get(
                user__username=validated_data["receiver"]
            )

            # Créer la transaction
            validated_data["status"] = TransactionStatus.SUCCESS.value
            
            TransactionService.create_pending_transaction(
                receiver=sender_wallet,
                receiver=receiver_wallet,
                transaction_type = TransactionType.TRANSFER.value,
                amount = validated_data["amount"],
                TransactionStatus.SUCCESS.value,
                order_by=TransactionService.generate_order_id(),
            )

            TransactionService.debit_wallet(
                sender_wallet, transaction.amount, transaction
            )
            TransactionService.credit_wallet(
                receiver_wallet, transaction.amount, transaction
            )

        else:
            partner = validated_data["partner"]
            description = f"Transfer VIA {partner}"
            transaction = TransactionService.create_pending_transaction(
                sender_wallet,
                None,
                TransactionType.TRANSFER.value,
                validated_data["amount"],
                description,
            )

            factory = PartnerGatewayFactory(partner)

            response = factory.process_transfer(
                transaction, receiver=validated_data["receiver"]
            )
            result = response.get("status", {})

            TransactionService.update_transaction_status(transaction, result.upper())
            if result != "success":
                raise PaymentProcessingError(
                    detail="Le traitement du transfer a échoué.",
                    code="PAYMENT_PROCESSING_ERROR",
                )

            TransactionService.debit_wallet(
                sender_wallet, transaction.amount, transaction, description
            )
            TransactionService.add_additional_data(transaction, response)

        return transaction


class MerchantPaymentSerializer(serializers.Serializer):
    merchant_code = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    details = serializers.JSONField(required=False)

    def validate(self, data):
        merchant = data.get("merchant_code")
        amount = data.get("amount")
        details = data.get("details") or {}

        # ✅ Vérif générique
        if amount <= 0:
            raise serializers.ValidationError(
                detail="Le montant doit être positif.", code="INVALID_AMOUNT"
            )

        # ✅ Lookup policy
        policy = MERCHANT_POLICIES.get(merchant)

        if policy:
            if policy.public:  # 🔹 Public → check des champs obligatoires
                missing = [f for f in policy.required_fields if f not in details]
                if missing:
                    raise serializers.ValidationError(
                        {
                            "details": f"Champs manquants pour {merchant.upper()} : {', '.join(missing)}"
                        }
                    )

        return data


class WalletBalanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletBalanceHistory
        fields = [
            "balance_before",
            "balance_after",
            "transaction_type",
            "timestamp",
            "description",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    balance_histories = WalletBalanceHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "transaction_type",
            "amount",
            "sender",
            "receiver",
            "timestamp",
            "description",
            "status",
            "balance_histories",
        ]


class TopUpSerializer(serializers.Serializer):
    PARTNER_DETAILS = {
        "ORANGE_MONEY": "Recharge via Orange Money",
        "MTN_MONEY": "Recharge via MTN Money",
        "WAVE": "Recharge via WAVE",
    }

    partner = serializers.CharField(max_length=50, required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        if data["partner"] not in self.PARTNER_DETAILS:
            raise serializers.ValidationError(
                detail="Partenaire non supporté", code="INSUPPORTED_PARTNER"
            )

        # Vérification du montant
        if data["amount"] <= 0:
            raise serializers.ValidationError(
                detail="Le montant doit être positif.", code="INVALID_AMOUNT"
            )

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        partner = validated_data["partner"]
        amount = validated_data["amount"]

        wallet = Wallet.objects.get(user=user)

        description = f"Rechargement VIA {partner}"
        order_id = TransactionService.generate_order_id(partner)
        transaction = TransactionService.create_pending_transaction(
            sender=None,
            receiver=wallet,
            transaction_type=TransactionType.TOPUP.value,
            amount=amount,
            description=description,
            order_id=order_id,
        )

        try:
            factory = PartnerGatewayFactory(partner)
            result = factory.process_top_up(transaction)
            status = result.get("status")
            if status != "PENDING":
                raise PaymentProcessingError(
                    detail="Le traitement du rechargement a échoué.",
                    code="PAYMENT_PROCESSING_ERROR",
                )

            TransactionService.update_transaction_status(transaction, status.upper())
            TransactionService.add_additional_data(transaction, result)

        except PaymentProcessingError as e:
            TransactionService.update_transaction_status(transaction, TransactionStatus.FAILED.value)
            raise serializers.ValidationError(detail=str(e), code="TRANSACTION_FAILED")
        return transaction
