import paho.mqtt.client as mqtt
import json
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MQTTService:
    """
    Service pour gérer les notifications MQTT via HiveMQ Cloud
    """
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MQTTService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialise la connexion MQTT"""
        try:
            self._client = mqtt.Client(client_id=f"pliz_backend_{os.getenv('HOSTNAME', 'local')}")
            
            # Configuration HiveMQ Cloud
            broker = os.getenv('MQTT_BROKER', 'broker.hivemq.com')
            port = int(os.getenv('MQTT_PORT', '1883'))
            username = os.getenv('MQTT_USERNAME', '')
            password = os.getenv('MQTT_PASSWORD', '')
            
            if username and password:
                self._client.username_pw_set(username, password)
            
            # Callbacks
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_publish = self._on_publish
            
            # Connexion
            self._client.connect(broker, port, keepalive=60)
            self._client.loop_start()
            
            logger.info(f"MQTT Service initialized - Broker: {broker}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MQTT: {e}")
            self._client = None
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback appelé lors de la connexion"""
        if rc == 0:
            logger.info("Connected to MQTT Broker successfully")
        else:
            logger.error(f"Failed to connect to MQTT Broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback appelé lors de la déconnexion"""
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Will auto-reconnect. RC: {rc}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback appelé après publication"""
        logger.debug(f"Message published successfully. MID: {mid}")
    
    def publish_notification(
        self, 
        user_uuid: str, 
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publie une notification pour un utilisateur
        
        Args:
            user_uuid: UUID de l'utilisateur
            notification_type: Type de notification (transaction, payment, topup, error, etc.)
            title: Titre de la notification
            message: Message de la notification
            data: Données additionnelles (optionnel)
        
        Returns:
            bool: True si la publication a réussi
        """
        if not self._client:
            logger.warning("MQTT client not initialized. Skipping notification.")
            return False
        
        try:
            topic = f"pliz/{user_uuid}/notifications"
            
            payload = {
                "type": notification_type,
                "title": title,
                "message": message,
                "timestamp": None,  # Will be set by timestamp on client side
                "data": data or {}
            }
            
            result = self._client.publish(
                topic,
                payload=json.dumps(payload),
                qos=1,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Notification sent to {user_uuid}: {notification_type}")
                return True
            else:
                logger.error(f"Failed to publish notification. RC: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing notification: {e}")
            return False
    
    def publish_merchant_notification(
        self,
        merchant_uuid: str,
        payment_data: Dict[str, Any]
    ) -> bool:
        """
        Publie une notification de paiement pour un marchand
        
        Args:
            merchant_uuid: UUID du marchand
            payment_data: Données du paiement
        
        Returns:
            bool: True si la publication a réussi
        """
        if not self._client:
            logger.warning("MQTT client not initialized. Skipping notification.")
            return False
        
        try:
            topic = f"pliz/{merchant_uuid}/payments"
            
            result = self._client.publish(
                topic,
                payload=json.dumps(payment_data),
                qos=1,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Payment notification sent to merchant {merchant_uuid}")
                return True
            else:
                logger.error(f"Failed to publish merchant notification. RC: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing merchant notification: {e}")
            return False
    
    def disconnect(self):
        """Déconnecte proprement du broker MQTT"""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("MQTT client disconnected")


# Instance singleton
mqtt_service = MQTTService()
