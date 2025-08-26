import os
import requests
import logging

logger = logging.getLogger(__name__)


class SamirPaymentGateway:
    """
    Connecteur pour effectuer des opérations Cashin et Cashout via l'API SAMIR.
    """

    BASE_URL = f'{os.environ.get("SAMIR_API_BASE_URL")}/api/tiers/payments/send'

    def __init__(self, partner="WAVE"):
        self.partner = partner

        self.api_key = os.environ.get("SAMIR_API_KEY")
        self.secret_key = os.environ.get("SAMIR_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Les variables d'environnement SAMIR_API_KEY et SAMIR_SECRET_KEY doivent être définies."
            )

    def _headers(self):
        return {
            "X-API-KEY": self.api_key,
            "X-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json",
        }

    def initiate_topup(
        self,
        transaction,
        description="Cashin depuis wallet",
    ):
        """
        Effectue un Cashin (dépôt d'argent depuis un wallet).
        """
        url = f"{self.BASE_URL}/cashin"

        payload = {
            "orderId": transaction.order_id,
            "amount": float(transaction.amount),
            "phoneNumber": transaction.sender.user.phone_number,
            "operatorName": self.partner,
            "description": description,
        }

        response = requests.post(url, headers=self._headers(), json=payload)

        try:
            response.raise_for_status()
            data = response.json()
            logger.info(f"Cashin response: {data}")
            return data
        except requests.HTTPError as e:
            logger.error(f"Cashin HTTP Error: {e} | Response: {response.text}")
            return {"error": str(e), "details": response.text}

    def initiate_transfer(
        self,
        transaction,
        receiver,
    ):
        """
        Effectue un Cashout (retrait d'argent vers un wallet).
        """
        url = f'{os.environ.get("SAMIR_API_BASE_URL")}/api/tiers/payments/send'
        payload = {
            "orderId": transaction.order_id,
            "amount": float(transaction.amount),
            "phoneNumber": receiver,
            "operatorName": self.partner,
        }

        response = requests.post(url, headers=self._headers(), json=payload)

        try:
            response.raise_for_status()
            data = response.json()
            logger.info(f"Cashout response: {data}")
            return data
        except requests.HTTPError as e:
            logger.error(f"Cashout HTTP Error: {e} | Response: {response.text}")
            return {"error": str(e), "details": response.text}
