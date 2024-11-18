from rest_framework.exceptions import APIException

class PaymentProcessingError(APIException):
    status_code = 500  # Le code de statut HTTP pour une erreur interne du serveur
    default_detail = 'Une erreur est survenue lors du traitement du paiement.'  # Détail par défaut de l'erreur
    default_code = 'payment_processing_error'  # Code d'erreur spécifique pour le traitement du paiement
