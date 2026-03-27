import pyotp
from django.core.mail import send_mail
from django.conf import settings
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
    def send_otp_by_sms(user_phone_number: str, otp: str) -> dict:
        """
        Envoie un code OTP par SMS via Twilio.

        Args:
            user_phone_number (str): Numéro de téléphone du destinataire (format international, ex: +221771234567).
            otp (str): Code OTP à envoyer.

        Returns:
            dict: Informations sur le message envoyé (sid, status).

        Raises:
            Exception: Si les credentials Twilio sont manquants ou si l'envoi échoue.
        """
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not account_sid or not auth_token or not from_number:
            raise Exception(
                "Les variables Twilio sont manquantes : "
                "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER."
            )

        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=f"Votre code OTP est : {otp}",
                from_=from_number,
                to=user_phone_number,
            )
            logger.info(f"SMS OTP sent via Twilio to {user_phone_number} (sid={message.sid})")
            return {"sid": message.sid, "status": message.status}

        except TwilioRestException as e:
            raise Exception(f"Échec de l'envoi du SMS via Twilio : {e}")
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
