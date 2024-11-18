from rest_framework import serializers
from actor.models import CustomUser, Wallet


class UserRegistrationSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True, max_length=15)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']

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
    def validate_email(self, value):
        """
        Validation personnalisée pour vérifier si l'email est unique.
        """
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        # Extraire le numéro de téléphone du sérialiseur
        phone_number = validated_data.pop('phone_number')

        # Création de l'utilisateur
        user = CustomUser.objects.create(
            username=phone_number,  # Utiliser le numéro de téléphone comme nom d'utilisateur
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            is_active=False  # Marquer le compte comme inactif par défaut
        )

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
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        try:
            CustomUser.objects.get(username=value)  # username est utilisé comme le numéro de téléphone
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Aucun utilisateur trouvé pour ce numéro de téléphone.")
        return value

class LoginWithOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

    def validate_phone_number(self, value):
        # Vérifier si l'utilisateur existe avec ce numéro de téléphone
        try:
            user = CustomUser.objects.get(username=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Utilisateur non trouvé.")
        self.context['user'] = user
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

        return user
