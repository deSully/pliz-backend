import os
import requests
import logging


logger = logging.getLogger(__name__)


class SamirPayMerchantPaymentProcessor:
    """
    Connecteur pour effectuer des opérations Cashin et Cashout via l'API SAMIR.
    """

    BASE_URL = f'{os.environ.get("SAMIR_API_BASE_URL")}/api/invoice/v1/WIZALL'

    def __init__(self, merchant_code="airtime"):
        self.merchant_code = merchant_code

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

    def _get_merchant_endpoint(self):
        match self.merchant_code:
            case "airtime":
                return f"{self.BASE_URL}/airtime-reload"
            case "woyofal":
                return f"{self.BASE_URL}/woyofal-reload"
            case "rapido-reload":
                return f"{self.BASE_URL}/rapido"

    def initiate_payment(
        self,
        transaction,
        details: dict,
    ):
        """
        Effectue un Cashout (retrait d'argent vers un wallet).
        """
        url = self._get_merchant_endpoint()
        payload = {
            "orderId": transaction.order_id,
            "amount": float(transaction.amount),
        }

        for detail in self.details:
            payload.update({detail: details[detail]})

        response = requests.post(url, headers=self._headers(), json=payload)

        try:
            response.raise_for_status()
            data = response.json()
            logger.info(f"Merchant payment response: {data}")
            return data
        except requests.HTTPError as e:
            logger.error(f"Cashout HTTP Error: {e} | Response: {response.text}")
            return {"error": str(e), "details": response.text}
