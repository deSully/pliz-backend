import pyotp
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import (
    Client,
)  # Exemple d'utilisation pour l'envoi par SMS (facultatif)
import os
import logging

logger = logging.getLogger(__name__)


class OTPService:
    @staticmethod
    def generate_otp(validity_duration=5):
        """
        Génère un OTP pour un utilisateur donné en utilisant pyotp.
        L'OTP est valide par défaut pendant 15 minutes, mais ce délai peut être modifié via le paramètre validity_duration.

        :param validity_duration: Durée de validité de l'OTP en minutes (par défaut 15).
        :return: Le code OTP généré.
        """
        # Clé secrète unique pour l'utilisateur
        secret = os.getenv("OTP_SECRET_KEY")

        # Paramétrage de la durée de validité de l'OTP (en secondes)
        totp = pyotp.TOTP(secret, interval=validity_duration * 60)

        # Générer l'OTP
        otp = totp.now()
        logger.info(f"Generated OTP: {otp}")

        return otp

    @staticmethod
    def validate_otp(otp, validity_duration=5) -> bool:
        """
        Valide un OTP en le comparant à celui généré avec pyotp.
        Retourne True si l'OTP est valide, sinon False.
        """
        secret = os.getenv("OTP_SECRET_KEY")
        totp = pyotp.TOTP(secret, interval=validity_duration * 60)

        result = totp.verify(otp)
        logger.info(f"OTP validation result: {result}")
        return result

    @staticmethod
    def send_otp_by_sms(user, otp):
        """
        Exemple d'envoi de l'OTP par SMS via Twilio.
        """

        twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

        # Utilisation de Twilio pour envoyer le SMS
        if twilio_phone_number is None or twilio_account_sid is None or twilio_auth_token is None:
            raise Exception(
                "Twilio credentials are not set. Please check your environment variables."
            )

        client = Client(twilio_account_sid, twilio_auth_token)
        message = client.messages.create(
            body=f"Votre code OTP est: {otp}",
            from_=twilio_phone_number,  # Numéro de téléphone Twilio
            to=user.phone_number,  # Numéro de téléphone de l'utilisateur
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
