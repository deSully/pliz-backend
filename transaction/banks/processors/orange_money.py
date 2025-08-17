import os
import requests
import base64



class OrangeMoneyGateway:
    """
    Connecteur pour effectuer des paiements via Orange Money.
    """

    BASE_URL = "https://api.orange.com/om-webpay/v1/webpayment"
    TOKEN_URL = "https://api.orange.com/oauth/v1/token"

    def __init__(self):
        self.merchant_key = os.environ.get("MERCHANT_KEY")
        self.client_id = os.environ.get("ORANGE_CLIENT_ID")
        self.client_secret = os.environ.get("ORANGE_CLIENT_SECRET")

        if not self.client_id or not self.client_secret or not self.merchant_key:
            raise ValueError(
                "Les variables d'environnement MERCHANT_KEY, ORANGE_CLIENT_ID et ORANGE_CLIENT_SECRET doivent être définies."
            )

        self.access_token = self._get_access_token()

    def _get_access_token(self):
        """
        Récupère le jeton d'accès OAuth 2.0 depuis Orange Money.
        """
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        response = requests.post(self.TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()["access_token"]


    def initiate_payment(
        self,
        order_id,
        amount,
        return_url,
        cancel_url,
        notif_url,
        detail=None,
        partner=None,
    ):
        """
        Initialise un paiement via Orange Money depuis l'app Pliiz.
        `detail` et `partner` peuvent servir à enrichir la description.
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        description = (
            f"Rechargement {partner}" if partner else "Rechargement compte Pliiz"
        )
        if detail:
            description += f" - {detail}"

        payload = {
            "merchant_key": self.merchant_key,
            "currency": "XOF",
            "order_id": order_id,
            "amount": amount,
            "description": description,
            "return_url": return_url,
            "cancel_url": cancel_url,
            "notif_url": notif_url,
        }

        response = requests.post(self.BASE_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def handle_notification(self, request_data):
        """
        Traite la notification de statut de paiement reçue d'Orange Money.
        """
        # Exemple : vérifier le statut et mettre à jour le compte Pliiz de l'utilisateur
        payment_status = request_data.get("status")
        order_id = request_data.get("order_id")
        # Ici tu peux ajouter la logique de mise à jour du compte
        return {"order_id": order_id, "status": payment_status}
