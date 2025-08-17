from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from .models import Transaction, WalletBalanceHistory
from actor.models import Wallet
from transaction.services.transaction import TransactionService

from transaction.errors import PaymentProcessingError

from transaction.banks.factory import TopUpFactory


import logging

logger = logging.getLogger(__name__)


class SendMoneySerializer(serializers.ModelSerializer):
    receiver = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Transaction
        fields = ["receiver", "amount"]
        read_only_fields = ["status"]

    def validate(self, data):
        logging.error(f"Validating data: {data}")

        # Vérification que le montant est positif
        if data["amount"] <= 0:
            raise serializers.ValidationError(
                detail="Le montant doit être positif.", code="INVALID_AMOUNT"
            )

        try:
            logging.error(f"Validating data: {data}")

            # Récupérer les wallets de l'envoyeur et du récepteur
            logger.error(f"Request context: {self.context['request']}")
            sender_wallet = Wallet.objects.get(user=self.context["request"].user)
            logging.error(f"Sender wallet: {sender_wallet}")
            receiver_wallet = Wallet.objects.get(phone_number=data["receiver"])
            logging.error(f"Receiver wallet: {receiver_wallet}")

            logging.error(
                f"Sender wallet: {sender_wallet}, Receiver wallet: {receiver_wallet}"
            )

            # Vérifier que l'envoyeur et le récepteur sont actifs (vérification de l'utilisateur lié au wallet)
            if not sender_wallet.user.is_active:
                raise serializers.ValidationError(
                    detail="L'utilisateur envoyeur est inactif.",
                    code="SENDER_INACTIVE_ERROR",
                )
            if not receiver_wallet.user.is_active:
                raise serializers.ValidationError(
                    detail="L'utilisateur bénéficiaire est inactif.",
                    code="RECEIVER_INACTIVE_ERROR",
                )

            # Vérification du solde de l'envoyeur
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
        sender_wallet = Wallet.objects.get(user=self.context["request"].user)
        receiver_wallet = Wallet.objects.get(user=validated_data["receiver"])

        # Création de la transaction
        validated_data["status"] = "completed"
        transaction = Transaction()
        transaction.receiver = receiver_wallet
        transaction.sender = sender_wallet
        transaction.amount = validated_data["amount"]
        transaction.transaction_type = "send"
        transaction.status = "completed"
        transaction.save()

        # Enregistrement des historiques de soldes
        TransactionService.debit_wallet(
            sender_wallet, validated_data["amount"], transaction
        )
        TransactionService.credit_wallet(
            receiver_wallet, validated_data["amount"], transaction
        )

        return transaction


class MerchantPaymentSerializer(serializers.Serializer):
    merchant_code = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    details = serializers.JSONField()

    def validate(self, data):
        """
        Validation générique pour tous les marchands.
        """
        if data["amount"] <= 0:
            raise serializers.ValidationError(
                detail="Le montant doit être positif.", code="INVALID_AMOUNT"
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
    }

    detail = serializers.CharField(max_length=255, required=False)
    partner = serializers.CharField(max_length=50, required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        if data["partner"] not in self.PARTNER_DETAILS:
            raise serializers.ValidationError(detail="Partenaire non supporté", code="INSUPPORTED_PARTNER")

        # Vérification du montant
        if data["amount"] <= 0:
            raise serializers.ValidationError(
                detail="Le montant doit être positif.", code="INVALID_AMOUNT"
            )

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        partner = validated_data["partner"]
        detail = validated_data["detail"]
        amount = validated_data["amount"]

        wallet = Wallet.objects.get(user=user)

        # 1. Créer la transaction en attente
        description = f"Rechargement depuis {partner} - {detail}"
        order_id = TransactionService.generate_order_id(partner)
        transaction = TransactionService.create_pending_transaction(
            sender=None,
            receiver=wallet,
            transaction_type="topup",
            amount=amount,
            description=description,
            order_id=order_id,
        )

        try:
            TopUpFactory.process_top_up(detail, transaction)

        except PaymentProcessingError as e:
            TransactionService.update_transaction_status(transaction, "failed")
            raise serializers.ValidationError(detail=str(e), code="TRANSACTION_FAILED")
        return transaction
