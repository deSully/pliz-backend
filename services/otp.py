import pyotp
import random
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client  # Exemple d'utilisation pour l'envoi par SMS (facultatif)

class OTPService:
    @staticmethod
    def generate_otp(user):
        """
        Génère un OTP pour un utilisateur donné en utilisant pyotp.
        Retourne le code OTP généré.
        """
        # Clé secrète unique pour l'utilisateur (par exemple, un hash ou une chaîne aléatoire)
        secret = OTPService.get_secret_for_user(user)

        # Création d'un générateur OTP avec pyotp
        totp = pyotp.TOTP(secret)

        # Générer l'OTP
        otp = totp.now()

        # Optionnel: Vous pouvez stocker l'OTP dans la base de données pour validation
        # par exemple, dans un champ ou une table dédiée.

        return otp

    @staticmethod
    def validate_otp(user, otp):
        """
        Valide un OTP en le comparant à celui généré avec pyotp.
        Retourne True si l'OTP est valide, sinon False.
        """
        secret = OTPService.get_secret_for_user(user)
        totp = pyotp.TOTP(secret)

        # Vérification de l'OTP (en tenant compte du temps de validité)
        return totp.verify(otp)

    @staticmethod
    def get_secret_for_user(user):
        """
        Génére et retourne une clé secrète pour l'utilisateur.
        Cette clé doit être unique pour chaque utilisateur et stockée de manière sécurisée.
        Pour la démonstration, on crée une clé secrète aléatoire ici.
        """
        # Pour la production, il est préférable de stocker cette clé secrète de manière sécurisée
        # dans un modèle de base de données, liée à l'utilisateur.
        return pyotp.random_base32()  # Génére une clé secrète aléatoire en base32

    @staticmethod
    def send_otp_by_sms(user, otp):
        """
        Exemple d'envoi de l'OTP par SMS via Twilio.
        """
        # Utilisation de Twilio pour envoyer le SMS
        if not settings.TWILIO_PHONE_NUMBER:
            raise Exception("Twilio phone number is not configured.")

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Votre code OTP est: {otp}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=user.phone_number  # Numéro de téléphone de l'utilisateur
        )
        return message.sid

    @staticmethod
    def send_otp_by_email(user, otp):
        """
        Envoie l'OTP à l'utilisateur par email.
        """
        subject = "Votre code OTP"
        message = f"Bonjour {user.first_name},\n\nVotre code OTP est: {otp}\n\nMerci!"
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
