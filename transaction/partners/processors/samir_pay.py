import os
import requests
import logging

logger = logging.getLogger(__name__)


class SamirPaymentGateway:
    """
    Connecteur pour effectuer des opérations Cashin et Cashout via l'API SAMIR.
    """


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
        transaction
    ):
        """
        Effectue un Cashin (dépôt d'argent depuis un wallet).
        """
        url = f'{os.environ.get("SAMIR_API_BASE_URL")}/api/tiers/initPayment'

        payload = {
            "orderId": transaction.order_id,
            "amount": float(transaction.amount),
            "telephone": transaction.receiver.user.phone_number,
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
            "amount": str(transaction.amount),
            "phoneNumber": receiver,
            "operatorName": self.partner,
        }

        logger.info(f"Initiating transfer with payload: {payload}")

        response = requests.post(url, headers=self._headers(), json=payload)

        logger.info(f"Samir transfer response status: {response.status_code}")
        logger.info(f"Samir transfer response text: {response.text}")
        logger.info(f"Samir transfer response headers: {response.headers}")
        logger.info(f"Samir transfer response url: {response.url}")
        logger.info(f"Samir transfer response request: {response.request.__dict__}")
        logger.info(f"Samir transfer response request body: {response.json()}")

        try:
            response.raise_for_status()
            data = response.json()
            logger.info(f"Cashout response: {data}")
            return data
        except requests.HTTPError as e:
            logger.error(f"Cashout HTTP Error: {e} | Response: {response.text}")
            return {"error": str(e), "details": response.text}
