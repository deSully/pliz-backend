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
            # Vérifier que les credentials MQTT sont configurés
            broker = os.getenv('MQTT_BROKER', '')
            port = int(os.getenv('MQTT_PORT', '1883'))
            username = os.getenv('MQTT_USERNAME', '')
            password = os.getenv('MQTT_PASSWORD', '')
            
            if not broker or not username or not password:
                logger.warning(
                    "MQTT credentials not configured. "
                    "Notifications will be disabled. "
                    "Set MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD env vars."
                )
                self._client = None
                return
            
            self._client = mqtt.Client(client_id=f"pliz_backend_{os.getenv('HOSTNAME', 'local')}")
            self._client.username_pw_set(username, password)
            
            # Callbacks
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_publish = self._on_publish
            
            # Connexion avec timeout
            self._client.connect(broker, port, keepalive=60)
            self._client.loop_start()
            
            logger.info(f"MQTT Service initialized - Broker: {broker}:{port}")
            
        except Exception as e:
            logger.error(
                f"Failed to initialize MQTT: {e}. "
                f"Notifications will be disabled but transactions will continue."
            )
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
    
    def publish_transaction_notification(
        self, 
        user_uuid: str,
        action: str,
        status: str,
        title: str,
        message: str,
        transaction_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publie une notification de transaction
        
        Args:
            user_uuid: UUID de l'utilisateur
            action: Action (send_money, receive_money, topup, payment)
            status: Statut (pending, success, failed)
            title: Titre de la notification
            message: Message de la notification
            transaction_data: Données de la transaction (optionnel)
        
        Returns:
            bool: True si la publication a réussi, False sinon (graceful degradation)
        """
        if not self._client:
            logger.warning(
                f"MQTT client not initialized. Skipping notification for {user_uuid}. "
                f"Transaction processing will continue normally."
            )
            return False
        
        try:
            topic = f"pliz/{user_uuid}/notifications"
            
            data = transaction_data or {}
            data["action"] = action
            data["status"] = status
            
            payload = {
                "type": "transaction",
                "title": title,
                "message": message,
                "data": data
            }
            
            result = self._client.publish(
                topic,
                payload=json.dumps(payload),
                qos=1,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Transaction notification sent to {user_uuid}: {action} - {status}")
                return True
            else:
                logger.warning(
                    f"Failed to publish notification to {user_uuid}. RC: {result.rc}. "
                    f"Transaction continues normally."
                )
                return False
                
        except Exception as e:
            logger.error(
                f"Error publishing notification to {user_uuid}: {e}. "
                f"Transaction continues normally (graceful degradation)."
            )
            return False
    
    def publish_system_notification(
        self,
        user_uuid: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publie une notification système
        
        Args:
            user_uuid: UUID de l'utilisateur
            title: Titre de la notification
            message: Message de la notification
            data: Données additionnelles (optionnel)
        
        Returns:
            bool: True si la publication a réussi, False sinon (graceful degradation)
        """
        if not self._client:
            logger.warning(
                f"MQTT client not initialized. Skipping system notification for {user_uuid}."
            )
            return False
        
        try:
            topic = f"pliz/{user_uuid}/notifications"
            
            payload = {
                "type": "system",
                "title": title,
                "message": message,
                "data": data or {}
            }
            
            result = self._client.publish(
                topic,
                payload=json.dumps(payload),
                qos=1,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"System notification sent to {user_uuid}")
                return True
            else:
                logger.warning(
                    f"Failed to publish system notification to {user_uuid}. RC: {result.rc}"
                )
                return False
                
        except Exception as e:
            logger.error(
                f"Error publishing system notification to {user_uuid}: {e}"
            )
            return False
    

    
    def disconnect(self):
        """Déconnecte proprement du broker MQTT"""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("MQTT client disconnected")


# Instance singleton
mqtt_service = MQTTService()
