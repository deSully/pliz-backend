import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class FirebaseService:
    """
    Service pour envoyer des notifications push via Firebase Cloud Messaging (FCM).
    Service pour les notifications push en temps réel.
    """

    _instance = None
    _app = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialise l'application Firebase Admin SDK"""
        try:
            import firebase_admin
            from firebase_admin import credentials

            credentials_file = os.getenv("FIREBASE_CREDENTIALS_FILE", "")

            if not credentials_file or not os.path.exists(credentials_file):
                logger.warning(
                    "Firebase credentials file not found or not configured. "
                    "Push notifications will be disabled. "
                    "Set FIREBASE_CREDENTIALS_FILE env var to the path of your service account JSON."
                )
                self._app = None
                return

            # Éviter la double initialisation
            if not firebase_admin._apps:
                cred = credentials.Certificate(credentials_file)
                self._app = firebase_admin.initialize_app(cred)
            else:
                self._app = firebase_admin.get_app()

            logger.info("Firebase Service initialized successfully")

        except ImportError:
            logger.error(
                "firebase-admin package not installed. "
                "Run: pip install firebase-admin"
            )
            self._app = None
        except Exception as e:
            logger.error(
                f"Failed to initialize Firebase: {e}. "
                f"Push notifications will be disabled but transactions will continue."
            )
            self._app = None

    def send_transaction_notification(
        self,
        fcm_token: Optional[str],
        action: str,
        status: str,
        title: str,
        message: str,
        transaction_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Envoie une notification de transaction via FCM.

        Args:
            fcm_token: Token FCM de l'appareil de l'utilisateur
            action: Action (send_money, receive_money, topup, payment)
            status: Statut (pending, success, failed)
            title: Titre de la notification
            message: Corps de la notification
            transaction_data: Données supplémentaires (optionnel)

        Returns:
            bool: True si envoi réussi, False sinon (graceful degradation)
        """
        if not self._app:
            logger.warning(
                "Firebase not initialized. Skipping push notification. "
                "Transactions continue normally."
            )
            return False

        if not fcm_token:
            logger.warning(
                f"No FCM token for this user (action={action}). "
                "User may not have registered their device token yet."
            )
            return False

        try:
            from firebase_admin import messaging

            data = transaction_data or {}
            data["action"] = action
            data["status"] = status
            # FCM data payload doit être dict[str, str]
            data_str = {k: str(v) for k, v in data.items() if v is not None}

            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=message,
                ),
                data=data_str,
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority="high",
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound="default"),
                    ),
                ),
            )

            response = messaging.send(fcm_message)
            logger.info(
                f"FCM notification sent (action={action}, status={status}): {response}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error sending FCM notification (action={action}): {e}. "
                f"Transaction continues normally (graceful degradation)."
            )
            return False

    def send_system_notification(
        self,
        fcm_token: Optional[str],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Envoie une notification système via FCM.

        Args:
            fcm_token: Token FCM de l'appareil
            title: Titre de la notification
            message: Corps de la notification
            data: Données supplémentaires (optionnel)

        Returns:
            bool: True si envoi réussi, False sinon (graceful degradation)
        """
        if not self._app:
            logger.warning("Firebase not initialized. Skipping system notification.")
            return False

        if not fcm_token:
            logger.warning("No FCM token provided for system notification.")
            return False

        try:
            from firebase_admin import messaging

            data_payload = data or {}
            data_payload["type"] = "system"
            data_str = {k: str(v) for k, v in data_payload.items() if v is not None}

            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=message,
                ),
                data=data_str,
                token=fcm_token,
            )

            response = messaging.send(fcm_message)
            logger.info(f"FCM system notification sent: {response}")
            return True

        except Exception as e:
            logger.error(f"Error sending FCM system notification: {e}")
            return False


# Instance singleton
firebase_service = FirebaseService()
