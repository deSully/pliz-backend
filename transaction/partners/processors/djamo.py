import os
import requests
import logging

from transaction.models import TransactionStatus

logger = logging.getLogger(__name__)


class DjamoPaymentGateway:
    """
    Connecteur pour effectuer des opérations Cashin et Cashout via l'API DJAMO.
    """

    def __init__(self, partner="WAVE"):
        self.partner = partner

        self.access_token = os.environ.get("DJAMO_ACCESS_TOKEN")
        self.secret_key = os.environ.get("DJAMO_SECRET_KEY")  # Pour vérifier les webhooks
        self.company_id = os.environ.get("DJAMO_COMPANY_ID")

        if not self.access_token:
            raise ValueError(
                "La variable d'environnement DJAMO_ACCESS_TOKEN doit être définie."
            )
        if not self.secret_key:
            raise ValueError(
                "La variable d'environnement DJAMO_SECRET_KEY doit être définie (pour webhooks)."
            )
        if not self.company_id:
            raise ValueError(
                "La variable d'environnement DJAMO_COMPANY_ID doit être définie."
            )
        
        self.base_url = f'{os.environ.get("DJAMO_API_BASE_URL", "https://api.djamo.io")}/v1/transaction'

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "X-company-Id": self.company_id
        }

    def initiate_transfer(
        self,
        transaction,
        receiver,
    ):
        """
        Recharge un wallet via DJAMO (Cashout).
        """

        description = f"Transfer Pliiz to {receiver}"
        payload = {
            "reference": transaction.order_id,
            "amount": float(transaction.amount),
            "msisdn": receiver,
            "description": description,
            "type": "transfer",
        }

        response = requests.post(self.base_url, headers=self._headers(), json=payload)

        try:
            response.raise_for_status()
            data = response.json()
            logger.info(f"Djamo payment response: {data}")
            return data
        except requests.HTTPError as e:
            logger.error(f"Cashout HTTP Error: {e} | Response: {response.text}")
            return {"status": TransactionStatus.FAILED.value, "details": response.text}

    def update_transaction_status(self, external_reference):
        """
        Vérifie le statut d'une transaction via l'API DJAMO.
        """
        url = f"{self.base_url}s/{external_reference}"

        response = requests.get(url, headers=self._headers())

        try:
            response.raise_for_status()
            data = response.json()
            logger.info(f"Djamo status response: {data}")
            return data
        except requests.HTTPError as e:
            logger.error(f"Status Check HTTP Error: {e} | Response: {response.text}")
            return {
                "status": TransactionStatus.FAILED.value,
                "details": response.text,
                "message": "Erreur lors de la vérification du statut de la transaction.",
            }
        except requests.RequestException as e:
            logger.error(f"Status Check Request Error: {e}")
            return {
                "status": TransactionStatus.FAILED.value,
                "details": str(e),
            }
