

from transaction.models import FeeDistribution, FeeDistributionRule
from actor.models import Merchant, Bank, Provider
from transaction.services.transaction import TransactionService
from transaction.utils import identify_wallet_owner

class FeeDistributionService:

    def identify_wallet_owner(wallet):
        if hasattr(wallet, "merchant"):
            return "merchant", wallet.merchant
        if hasattr(wallet, "bank"):
            return "bank", wallet.bank
        if hasattr(wallet, "provider"):
            return "provider", wallet.provider
        return "client", None


    @staticmethod
    def distribute_fee(transaction):
        fee_amount = transaction.fee_applied
        if not fee_amount or fee_amount == 0:
            return

        tx_type = transaction.transaction_type

        _, sender_owner = identify_wallet_owner(transaction.sender)
        _, receiver_owner = identify_wallet_owner(transaction.receiver)

        # Qui est qui ?
        merchant = sender_owner if isinstance(sender_owner, Merchant) else receiver_owner if isinstance(receiver_owner, Merchant) else None
        bank = sender_owner if isinstance(sender_owner, Bank) else receiver_owner if isinstance(receiver_owner, Bank) else None
        provider = sender_owner if isinstance(sender_owner, Provider) else receiver_owner if isinstance(receiver_owner, Provider) else None

        # Recherche de la règle de répartition
        rule = FeeDistributionService._get_applicable_rule(tx_type, merchant, bank)

        distributions = []

        def create_distribution(actor_type, actor, percentage):
            amount = round((percentage / 100) * fee_amount, 2)
            if amount > 0 and actor:
                FeeDistribution.objects.create(
                    transaction=transaction,
                    actor_type=actor_type,
                    actor_id=actor.id,
                    amount=amount
                )
                TransactionService.credit_wallet(actor.wallet, amount, transaction, "Part des frais")
                distributions.append((actor_type, actor.id, amount))

        if rule.provider_percentage and provider:
            create_distribution("provider", provider, rule.provider_percentage)
        if rule.bank_percentage and bank:
            create_distribution("bank", bank, rule.bank_percentage)
        if rule.merchant_percentage and merchant:
            create_distribution("merchant", merchant, rule.merchant_percentage)

        return distributions

    @staticmethod
    def _get_applicable_rule(tx_type, merchant=None, bank=None):
        rule = FeeDistributionRule.objects.filter(
            transaction_type=tx_type,
            merchant=merchant,
            is_active=True
        ).first()
        if rule:
            return rule

        rule = FeeDistributionRule.objects.filter(
            transaction_type=tx_type,
            bank=bank,
            is_active=True
        ).first()
        if rule:
            return rule

        return FeeDistributionRule.objects.filter(
            transaction_type=tx_type,
            merchant__isnull=True,
            bank__isnull=True,
            is_active=True
        ).first()
