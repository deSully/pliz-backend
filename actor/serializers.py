from rest_framework import serializers
from actor.models import CustomUser, Wallet, RIB


class UserRegistrationSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True, max_length=15)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number', 'password']

    def validate_phone_number(self, value):
        """
        Validation personnalisée pour vérifier si le numéro de téléphone est unique dans CustomUser et Wallet.
        """
        # Vérifier si le numéro existe déjà dans CustomUser
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé pour un utilisateur.")

        # Vérifier si le numéro existe déjà dans Wallet
        if Wallet.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé pour un portefeuille.")

        return value
    

    def create(self, validated_data):
        # Extraire le numéro de téléphone du sérialiseur
        phone_number = validated_data.pop('phone_number')

        # Création de l'utilisateur
        user = CustomUser.objects.create(
            username=phone_number,  # Utiliser le numéro de téléphone comme nom d'utilisateur
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=False  # Marquer le compte comme inactif par défaut
        )
        
        # Find a way to hash the password
        user.set_password(validated_data.get('password', None))
        user.save()

        # Créer un wallet pour l'utilisateur
        Wallet.objects.create(user=user, phone_number=phone_number)

        return user

class AccountActivationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True, max_length=15)
    otp = serializers.CharField(required=True, max_length=6)

    def validate_phone_number(self, value):
        """
        Validation personnalisée pour vérifier si le numéro de téléphone est unique dans CustomUser et Wallet.
        """
        # Vérifier si le numéro existe déjà dans CustomUser
        if CustomUser.objects.filter(username=value, is_active=True).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé et activé pour un utilisateur.")
        return value

    def get_user(self):
        """
        Retourner l'utilisateur à partir du numéro de téléphone.
        Si l'utilisateur n'existe pas ou est déjà actif, lever une exception.
        """
        phone_number = self.validated_data['phone_number']
        try:
            user = CustomUser.objects.get(username=phone_number)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Aucun utilisateur trouvé pour ce numéro de téléphone.")

        # Vérifier si l'utilisateur est déjà actif
        if user.is_active:
            raise serializers.ValidationError("Ce compte est déjà actif.")

        return user


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class CheckOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=6)
    phone_number = serializers.CharField(max_length=15)


class RIBSerializer(serializers.ModelSerializer):
    class Meta:
        model = RIB
        fields = [
            'banque', 'bank_code', 'code_guichet',
            'numero_compte', 'cle_rib', 'titulaire', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']