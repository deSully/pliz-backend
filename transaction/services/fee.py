from decimal import Decimal
from transaction.models import Fee
from actor.models import Wallet
from transaction.services.transaction import TransactionService


class FeeService:

    @staticmethod
    def get_applicable_fee(transaction_type, merchant=None, bank=None):
        """
        Recherche la règle de frais la plus spécifique à la plus générique.
        """
        # Recherche la règle la plus spécifique d'abord
        if merchant:
            rule = Fee.objects.filter(
                transaction_type=transaction_type,
                merchant=merchant,
                is_active=True
            ).first()
            if rule:
                return rule

        if bank:
            rule = Fee.objects.filter(
                transaction_type=transaction_type,
                bank=bank,
                is_active=True
            ).first()
            if rule:
                return rule

        # Sinon on cherche une règle générale
        return Fee.objects.filter(
            transaction_type=transaction_type,
            merchant__isnull=True,
            bank__isnull=True,
            is_active=True
        ).first()

    @staticmethod
    def calculate_fee_amount(fee, amount):
        """
        Calcule le montant du frais à partir de la règle.
        """
        total = Decimal("0.00")
        if fee:
            if fee.percentage:
                total += (amount * fee.percentage / Decimal("100"))
            if fee.fixed_amount:
                total += fee.fixed_amount
        return total.quantize(Decimal("0.01"))

    @staticmethod
    def apply_fee(user, wallet, transaction, transaction_type, merchant=None, bank=None):
        """
        Applique le frais si l’utilisateur n’est pas abonné.
        """
        if hasattr(user, "is_subscribed") and user.is_subscribed:
            return Decimal("0.00")

        fee = FeeService.get_applicable_fee(transaction_type, merchant=merchant, bank=bank)
        amount = transaction.amount
        fee_amount = FeeService.calculate_fee_amount(fee, amount)

        if fee_amount > 0:
            # Débit du wallet client
            TransactionService.debit_wallet(wallet, fee_amount, transaction, "Frais de transaction")

            # Crédit du wallet de la plateforme
            platform_wallet = Wallet.objects.get(is_platform=True)
            TransactionService.credit_wallet(platform_wallet, fee_amount, transaction, "Frais collecté")

        return fee_amount
