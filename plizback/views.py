from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
import os
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint pour monitoring
    Vérifie : Database, Firebase FCM, Environment
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

    # Vérifier Firebase FCM
    try:
        from services.firebase import firebase_service
        if firebase_service._app:
            health_status["checks"]["firebase"] = {
                "status": "healthy",
                "message": "Firebase FCM initialized"
            }
        else:
            health_status["checks"]["firebase"] = {
                "status": "degraded",
                "message": "Firebase not initialized (push notifications disabled)"
            }
    except Exception as e:
        health_status["checks"]["firebase"] = {
            "status": "degraded",
            "message": f"Firebase check failed: {str(e)}"
        }
        logger.warning(f"Health check - Firebase check failed: {e}")

    # Vérifier l'environnement
    health_status["environment"] = "production" if not os.getenv("DEBUG", "True") == "True" else "development"

    # Status global
    if not all_healthy:
        health_status["status"] = "unhealthy"
        return JsonResponse(health_status, status=503)
    
    return JsonResponse(health_status, status=200)
