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
            raise serializers.ValidationError(
                detail="Ce numéro de téléphone est déjà utilisé pour un utilisateur.",
                code="PHONE_ALREADY_EXISTS"
            )

        # Vérifier si le numéro existe déjà dans Wallet
        if Wallet.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                detail="Ce numéro de téléphone est déjà utilisé pour un portefeuille.",
                code="WALLET_PHONE_ALREADY_EXISTS"
            )

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
        wallet = Wallet.objects.create(user=user, phone_number=phone_number)
        
        # Initialiser le balance à 0
        from transaction.models import WalletBalanceHistory
        WalletBalanceHistory.objects.create(
            wallet=wallet,
            balance_before=0,
            balance_after=0,
            transaction_type="INIT",
            description="Initialisation du portefeuille"
        )

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
            raise serializers.ValidationError(
                detail="Ce numéro de téléphone est déjà utilisé et activé pour un utilisateur.",
                code="USER_PHONE_ALREADY_ACTIVE"
            )
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
            raise serializers.ValidationError(
                detail="Aucun utilisateur trouvé pour ce numéro de téléphone.",
                code="USER_NOT_FOUND"
            )

        # Vérifier si l'utilisateur est déjà actif
        raise serializers.ValidationError(
            detail="Ce compte est déjà actif.",
            code="ACCOUNT_ALREADY_ACTIVE"
        )

        return user


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class CheckOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=6)
    phone_number = serializers.CharField(max_length=15)


class MerchantRegistrationSerializer(serializers.ModelSerializer):
    # Informations utilisateur
    phone_number = serializers.CharField(required=True, max_length=15)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    # Informations marchand
    business_name = serializers.CharField(required=True, max_length=255)
    address = serializers.CharField(required=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number', 'password',
            'business_name', 'address'
        ]
    
    def validate_phone_number(self, value):
        """
        Validation pour vérifier si le numéro de téléphone est unique.
        """
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                detail="Ce numéro de téléphone est déjà utilisé.",
                code="PHONE_ALREADY_EXISTS"
            )
        
        if Wallet.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                detail="Ce numéro de téléphone est déjà utilisé pour un portefeuille.",
                code="WALLET_PHONE_ALREADY_EXISTS"
            )
        
        return value
    
    def create(self, validated_data):
        from actor.models import Merchant
        import uuid
        
        # Extraire les données
        phone_number = validated_data.pop('phone_number')
        business_name = validated_data.pop('business_name')
        address = validated_data.pop('address')
        password = validated_data.pop('password')
        
        # Créer l'utilisateur marchand
        user = CustomUser.objects.create(
            username=phone_number,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            user_type='merchant',
            is_active=False  # Inactif jusqu'à validation OTP
        )
        
        user.set_password(password)
        user.save()
        
        # Créer le wallet
        wallet = Wallet.objects.create(user=user, phone_number=phone_number)
        
        # Initialiser le balance à 0
        from transaction.models import WalletBalanceHistory
        WalletBalanceHistory.objects.create(
            wallet=wallet,
            balance_before=0,
            balance_after=0,
            transaction_type="INIT",
            description="Initialisation du portefeuille marchand"
        )
        
        # Générer un merchant_code unique
        merchant_code = f"MCH{str(uuid.uuid4())[:8].upper()}"
        
        # Créer le profil marchand
        Merchant.objects.create(
            wallet=wallet,
            merchant_code=merchant_code,
            business_name=business_name,
            address=address
        )
        
        return user


class RIBSerializer(serializers.ModelSerializer):
    class Meta:
        model = RIB
        fields = [
            'banque', 'bank_code', 'code_guichet',
            'numero_compte', 'cle_rib', 'titulaire', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher le profil complet de l'utilisateur
    """
    wallet = serializers.SerializerMethodField()
    merchant = serializers.SerializerMethodField()
    uuid = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'uuid', 'username', 'phone_number', 'first_name', 'last_name',
            'email', 'user_type', 'is_subscribed', 'wallet', 'merchant'
        ]
        read_only_fields = ['id', 'uuid', 'username', 'user_type']
    
    def get_phone_number(self, obj):
        return obj.username
    
    phone_number = serializers.SerializerMethodField()
    
    def get_wallet(self, obj):
        try:
            wallet = obj.wallet
            
            # Récupérer le solde actuel depuis WalletBalanceHistory
            from transaction.models import WalletBalanceHistory
            try:
                last_balance = WalletBalanceHistory.objects.filter(
                    wallet=wallet
                ).latest('timestamp')
                balance = float(last_balance.balance_after)
            except WalletBalanceHistory.DoesNotExist:
                balance = 0.0
            
            return {
                "id": wallet.id,  # ⭐ IMPORTANT: wallet_id pour les transactions
                "phone_number": wallet.phone_number,
                "currency": wallet.currency,
                "balance": balance,
                "is_platform": wallet.is_platform
            }
        except Exception:
            return None
    
    def get_merchant(self, obj):
        if obj.user_type == "merchant":
            try:
                from actor.models import Merchant
                merchant = Merchant.objects.get(wallet__user=obj)
                return {
                    "merchant_code": merchant.merchant_code,
                    "business_name": merchant.business_name,
                    "address": merchant.address
                }
            except Merchant.DoesNotExist:
                return None
        return None