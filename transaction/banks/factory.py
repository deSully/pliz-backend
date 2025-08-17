from .processors.ecobank import EcobankGateway
from .processors.orange_money import OrangeMoneyGateway
from .processors.mtn_money import (
    MtnMoneyGateway,
)  # Assuming MTN Money uses the same gateway as Orange Money


class TopUpFactory:
    """
    Factory pour gérer le rechargement du compte en fonction de la banque sélectionnée.
    """

    @staticmethod
    def get_gateway(partner):
        """
        Récupère le connecteur du partner.
        """
        if partner == "ORANGE_MONEY":
            return OrangeMoneyGateway()
        elif partner == "MTN_MONEY":
            return MtnMoneyGateway()
        elif partner == "ECOBANK":
            return EcobankGateway()
        else:
            raise ValueError(f"Partenaire {partner} non supporté.")

    @staticmethod
    def process_top_up(partner, transaction, amount):
        """
        Traite le rechargement en appelant la méthode debit de la banque sélectionnée.
        """
        partner_gateway = TopUpFactory.get_gateway(partner)
        partner_gateway.initiate_payment(transaction, amount) 
