from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
import os


def health_check(request):
    """
    Health check endpoint pour monitoring
    Vérifie la connexion à la DB et retourne le statut de l'API
    """
    health_status = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "service": "Pliz Money API",
        "version": "1.0.0",
    }

    # Vérifier la connexion à la base de données
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"error: {str(e)}"
        return JsonResponse(health_status, status=503)

    # Vérifier l'environnement
    health_status["environment"] = "production" if not os.getenv("DEBUG", "True") == "True" else "development"

    return JsonResponse(health_status, status=200)
