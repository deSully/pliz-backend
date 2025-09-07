from .processors.ecobank import EcobankGateway
from .processors.samir_pay import SamirPaymentGateway
from .processors.mtn_money import (
    MtnMoneyGateway,
)
from .processors.djamo import DjamoPaymentGateway


class PartnerGatewayFactory:
    """
    Factory pour gérer le rechargement du compte en fonction de la banque sélectionnée.
    """

    def __init__(self, partner: str):
        self.partner = partner
        self.gateway = self._get_gateway()

    def _get_gateway(self):
        """
        Retourne le connecteur correspondant au partenaire.
        """
        if self.partner in ["ORANGE_MONEY", "WAVE"]:
            return SamirPaymentGateway(partner=self.partner)
        elif self.partner == "MTN_MONEY":
            return MtnMoneyGateway()
        elif self.partner == "DJAMO":
            return DjamoPaymentGateway(partner=self.partner)
        elif self.partner == "ECOBANK":
            return EcobankGateway()
        else:
            raise ValueError(f"Partenaire {self.partner} non supporté.")

    def process_top_up(self, transaction):
        """
        Traite le rechargement (cash-in).
        """
        return self.gateway.initiate_topup(transaction)

    def process_transfer(self, transaction, receiver: str):
        """
        Traite le transfert (cash-out).
        """
        return self.gateway.initiate_transfer(transaction, receiver)
