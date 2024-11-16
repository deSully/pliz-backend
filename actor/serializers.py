from rest_framework import serializers
from .models import CustomUser, Wallet

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']

    def create(self, validated_data):
        # Création de l'utilisateur
        user = CustomUser.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            is_active=False  # Par défaut, l'utilisateur est inactif
        )

        # Création du Wallet pour l'utilisateur
        Wallet.objects.create(user=user, phone_number=validated_data['phone_number'])

        return user
