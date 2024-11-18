from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from .models import Transaction, WalletBalanceHistory
from actor.models import Wallet
from transaction.services.transaction import TransactionService


class SendMoneySerializer(serializers.ModelSerializer):

    receiver = serializers.CharField()
    sender = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Transaction
        fields = ['receiver', 'amount', 'sender']
        read_only_fields = ['status']

    def validate(self, data):
        try:
            # Récupérer les wallets de l'envoyeur et du récepteur
            sender_wallet = Wallet.objects.get(user=data['sender'])
            receiver_wallet = Wallet.objects.get(user=data['receiver'])

            # Vérifier que l'envoyeur et le récepteur sont actifs (vérification de l'utilisateur lié au wallet)
            if not sender_wallet.user.is_active:
                raise serializers.ValidationError("L'utilisateur envoyeur est inactif.")
            if not receiver_wallet.user.is_active:
                raise serializers.ValidationError("L'utilisateur récepteur est inactif.")

            # Vérification du solde de l'envoyeur
            TransactionService.check_sufficient_funds(sender_wallet, data['amount'])

        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Un des portefeuilles spécifiés n'existe pas.")
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Un des utilisateurs spécifiés n'existe pas.")
        except serializers.ValidationError as e:
            raise serializers.ValidationError(str(e))

        return data

    def create(self, validated_data):
        sender_wallet = Wallet.objects.get(user=validated_data['sender'])
        receiver_wallet = Wallet.objects.get(user=validated_data['receiver'])

        # Création de la transaction
        validated_data['status'] = 'completed'
        transaction = Transaction()
        transaction.receiver = receiver_wallet
        transaction.sender = sender_wallet
        transaction.amount = validated_data['amount']
        transaction.transaction_type = 'send'
        transaction.status = 'completed'
        transaction.save()

        # Enregistrement des historiques de soldes
        TransactionService.debit_wallet(sender_wallet, validated_data['amount'], transaction)
        TransactionService.credit_wallet(receiver_wallet, validated_data['amount'], transaction)

        return transaction

class MerchantPaymentSerializer(serializers.Serializer):
    merchant_code = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    details = serializers.JSONField()

    def validate(self, data):
        """
        Validation générique pour tous les marchands.
        """
        if data['amount'] <= 0:
            raise serializers.ValidationError({"amount": "Le montant doit être positif."})

        return data

class WalletBalanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletBalanceHistory
        fields = ['balance_before', 'balance_after', 'transaction_type', 'timestamp', 'description']


class TransactionSerializer(serializers.ModelSerializer):
    balance_histories = WalletBalanceHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'amount', 'sender', 'receiver', 'timestamp', 'description', 'status', 'balance_histories']
