from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from .models import Transaction, WalletBalanceHistory
from actor.models import Wallet
from transaction.services.transaction import TransactionService

from transaction.errors import PaymentProcessingError

from transaction.banks.factory import TopUpFactory

from actor.models import RIB

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
        try:

            logging.info(f"Validating data: {data}")
            
            # Récupérer les wallets de l'envoyeur et du récepteur
            sender_wallet = Wallet.objects.get(user=self.context["request"].user)
            receiver_wallet = Wallet.objects.get(user=data["receiver"])

            logging.info(f"Sender wallet: {sender_wallet}, Receiver wallet: {receiver_wallet}")



            # Vérifier que l'envoyeur et le récepteur sont actifs (vérification de l'utilisateur lié au wallet)
            if not sender_wallet.user.is_active:
                raise serializers.ValidationError("L'utilisateur envoyeur est inactif.")
            if not receiver_wallet.user.is_active:
                raise serializers.ValidationError(
                    "L'utilisateur récepteur est inactif."
                )

            # Vérification du solde de l'envoyeur
            TransactionService.check_sufficient_funds(sender_wallet, data["amount"])

        except Wallet.DoesNotExist:
            raise serializers.ValidationError(
                "Un des portefeuilles spécifiés n'existe pas."
            )
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "Un des utilisateurs spécifiés n'existe pas."
            )
        except serializers.ValidationError as e:
            raise serializers.ValidationError(str(e))

        return data

    def create(self, validated_data):
        sender_wallet = Wallet.objects.get(user=validated_data["sender"])
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
                {"amount": "Le montant doit être positif."}
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
    rib_uuid = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        user = self.context['request'].user

        # Vérification du RIB
        try:
            rib = RIB.objects.get(uuid=data['rib_uuid'], user=user)
        except RIB.DoesNotExist:
            raise serializers.ValidationError("Ce RIB n'existe pas ou ne vous appartient pas.")

        # Vérification du montant
        if data['amount'] <= 0:
            raise serializers.ValidationError("Le montant doit être supérieur à zéro.")

        # Attacher le RIB à la donnée validée
        data['rib'] = rib
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        rib = validated_data['rib']
        amount = validated_data['amount']
        wallet = Wallet.objects.get(user=user)

        # 1. Créer la transaction en attente
        description = f"Rechargement depuis RIB {rib.banque} - {rib.numero_compte}"
        transaction = TransactionService.create_pending_transaction(
            sender=None,  # Car la source est externe (RIB)
            receiver=wallet,
            transaction_type='topup',
            amount=amount,
            description=description,
        )

        try:
            # 2. Débiter le compte bancaire via l'API spécifique
            # Utilisation de TopUpFactory pour traiter la recharge
            TopUpFactory.process_top_up(rib, amount)

            # 3. Créditer le wallet du client
            TransactionService.credit_wallet(wallet, amount, transaction, description)

            # 4. Mettre à jour le statut de la transaction
            TransactionService.update_transaction_status(transaction, 'success')

        except PaymentProcessingError as e:
            # Si une erreur survient, annuler la transaction
            TransactionService.update_transaction_status(transaction, 'failed')
            raise serializers.ValidationError(str(e))

        return transaction
