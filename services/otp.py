import pyotp
import requests
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
        Envoie un code OTP par SMS à l'utilisateur via l'API SMPP (https://sms-api.smpp.app).

        Args:
            user_phone_number (str): Numéro de téléphone du destinataire (au format international).
            otp (str): Code OTP à envoyer.

        Returns:
            dict: Réponse JSON de l'API.

        Raises:
            Exception: Si une erreur survient lors de l'appel API.
        """

        # Configuration
        sms_api_url = "https://sms-api.smpp.app/v1/send-sms"
        sms_api_token = os.getenv("SMPP_API_TOKEN")  # À définir dans l'environnement
        sms_sender_id = os.getenv("SMPP_SENDER_ID", "MyApp")  # Nom de l'expéditeur

        if not sms_api_token:
            raise Exception("Le token SMPP_API_TOKEN est manquant dans les variables d'environnement.")

        # Préparation de la requête
        headers = {
            "Authorization": f"Bearer {sms_api_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "to": user_phone_number,
            "sender_id": sms_sender_id,
            "message": f"Votre code OTP est : {otp}"
        }

        # Envoi de la requête
        response = requests.post(sms_api_url, json=payload, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Échec de l'envoi du SMS : {response.status_code} - {response.text}")

        return response.json()
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
