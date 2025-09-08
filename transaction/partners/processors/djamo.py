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

        self.api_key = os.environ.get("DJAMO_API_KEY")
        self.secret_key = os.environ.get("DJAMO_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Les variables d'environnement DJAMO_API_KEY et DJAMO_SECRET_KEY doivent être définies."
            )
        self.base_url = f'{os.environ.get("DJAMO_API_BASE_URL")}/v1/transaction'

    def _headers(self):
        return {
            "X-API-KEY": self.api_key,
            "X-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json",
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
