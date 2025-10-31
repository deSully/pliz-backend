from rest_framework import serializers
from actor.models import CustomUser, Wallet


class MerchantInitiatedPaymentSerializer(serializers.Serializer):
    """
    Serializer pour les paiements initiés par un marchand.
    Le marchand scanne le QR code du client et envoie son numéro de téléphone.
    """
    customer_phone = serializers.CharField(max_length=15, required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_customer_phone(self, value):
        """
        Vérifie que le numéro de téléphone du client existe et est actif.
        """
        if not CustomUser.objects.filter(username=value, is_active=True).exists():
            raise serializers.ValidationError(
                detail="Ce numéro de téléphone n'existe pas ou n'est pas actif.",
                code="CUSTOMER_NOT_FOUND"
            )
        return value

    def validate_amount(self, value):
        """
        Vérifie que le montant est positif.
        """
        if value <= 0:
            raise serializers.ValidationError(
                detail="Le montant doit être supérieur à zéro.",
                code="INVALID_AMOUNT"
            )
        return value

    def validate(self, data):
        """
        Validation globale : vérifier que le client a un wallet.
        """
        customer_phone = data.get("customer_phone")
        try:
            customer = CustomUser.objects.get(username=customer_phone)
            wallet = Wallet.objects.get(user=customer)
            data["customer_wallet"] = wallet
        except Wallet.DoesNotExist:
            raise serializers.ValidationError(
                detail="Le client n'a pas de portefeuille.",
                code="WALLET_NOT_FOUND"
            )
        
        return data
