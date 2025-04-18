from .processors.ecobank import EcobankGateway


class TopUpFactory:
    """
    Factory pour gérer le rechargement du compte en fonction de la banque sélectionnée.
    """

    @staticmethod
    def get_gateway(bank_name):
        """
        Récupère le connecteur de banque en fonction du nom de la banque.
        """
        if bank_name == "Ecobank":
            return EcobankGateway()
        else:
            raise ValueError(f"Banque {bank_name} non supportée.")

    @staticmethod
    def process_top_up(rib, amount):
        """
        Traite le rechargement en appelant la méthode debit de la banque sélectionnée.
        """
        bank_gateway = TopUpFactory.get_gateway(rib.banque)  # Choisir la banque
        bank_gateway.debit(
            rib, amount
        )  # Appeler la méthode debit de la banque sélectionnée
