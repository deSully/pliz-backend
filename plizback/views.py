from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
import os
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint pour monitoring
    Vérifie : Database, MQTT, Environment
    """
    health_status = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "service": "Pliz Money API",
        "version": "1.0.0",
        "checks": {}
    }

    all_healthy = True

    # Vérifier la connexion à la base de données
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection OK"
        }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        logger.error(f"Health check - Database failed: {e}")

    # Vérifier MQTT
    try:
        from services.mqtt import mqtt_service
        if mqtt_service._client:
            health_status["checks"]["mqtt"] = {
                "status": "healthy",
                "message": "MQTT client initialized"
            }
        else:
            health_status["checks"]["mqtt"] = {
                "status": "degraded",
                "message": "MQTT client not initialized (graceful degradation active)"
            }
    except Exception as e:
        health_status["checks"]["mqtt"] = {
            "status": "degraded",
            "message": f"MQTT check failed: {str(e)}"
        }
        logger.warning(f"Health check - MQTT check failed: {e}")

    # Vérifier l'environnement
    health_status["environment"] = "production" if not os.getenv("DEBUG", "True") == "True" else "development"

    # Status global
    if not all_healthy:
        health_status["status"] = "unhealthy"
        return JsonResponse(health_status, status=503)
    
    return JsonResponse(health_status)

    return JsonResponse(health_status, status=200)
