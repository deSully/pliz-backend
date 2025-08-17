class BankGateway:
    """
    Classe de base pour les connecteurs de banques.
    Chaque connecteur de banque doit implémenter la méthode `debit`.
    """
    def debit(self, rib, amount):
        raise NotImplementedError("La méthode `debit` doit être implémentée dans la sous-classe.")

