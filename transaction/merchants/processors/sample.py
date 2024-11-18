from transaction.errors import PaymentProcessingError
from transaction.services.transaction import TransactionService
from dataclasses import dataclass

@dataclass
class SampleMerchantPaymentProcessor:
    merchant_code: str

    def process_payment(self, transaction, amount, details):
        # Traitement spécifique pour XXX
        # Par exemple, appeler une API, faire des calculs, etc.

        api_response = None
        if api_response.get('status') == 'success':
           pass
        else:
            raise PaymentProcessingError("Le paiement au marchand XXX a échoué.")
