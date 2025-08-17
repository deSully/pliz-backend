
class OrangeMoneyGateway:
    """
    Connecteur spécifique pour Orange money .
    """
    def debit(self, rib, amount):
        # Logique spécifique pour débiter BankXYZ
        print(f"Débit de {amount} sur le RIB {rib.numero_compte} pour BankXYZ.")