from decimal import Decimal
from django.db import transaction as db_transaction
from transaction.models import Fee, FeeDistributionRule, FeeDistribution
from actor.models import Wallet
from transaction.services.transaction import TransactionService
from transaction.models import TariffGrid
import logging

logger = logging.getLogger(__name__)


class FeeService:
    @staticmethod
    def get_applicable_fee(transaction_type, amount, merchant=None, bank=None):
        grid = TariffGrid.objects.filter(is_active=True).first()
        filters = {
            "tariff_grid": grid,
            "transaction_type": transaction_type,
            "min_amount__lte": amount,
            "max_amount__gte": amount,
            "is_active": True,
        }

        # 1. Chercher le plus spécifique
        if merchant:
            fee = Fee.objects.filter(**filters, merchant=merchant).first()
            if fee:
                return fee

        if bank:
            fee = Fee.objects.filter(**filters, bank=bank).first()
            if fee:
                return fee

        # 2. Fallback global
        return Fee.objects.filter(
            **filters, merchant__isnull=True, bank__isnull=True
        ).first()

    @staticmethod
    def calculate_fee_amount(fee, amount):
        """
        Calcule le montant du frais à partir de la règle.
        """
        total = Decimal("0.00")
        if fee:
            if fee.percentage:
                total += amount * fee.percentage / Decimal("100")
            if fee.fixed_amount:
                total += fee.fixed_amount
        return total.quantize(Decimal("0.01"))

    @staticmethod
    @db_transaction.atomic
    def apply_fee(
        user, wallet, transaction, transaction_type, merchant=None, bank=None
    ):
        """
        Applique le frais si l'utilisateur n'est pas abonné.
        Gère également la distribution des frais entre les acteurs.
        """
        if hasattr(user, "is_subscribed") and user.is_subscribed:
            return Decimal("0.00")

        fee = FeeService.get_applicable_fee(
            transaction_type, merchant=merchant, bank=bank
        )
        amount = transaction.amount
        fee_amount = FeeService.calculate_fee_amount(fee, amount)

        if fee_amount > 0:
            # Débit du wallet client
            TransactionService.debit_wallet(
                wallet, fee_amount, transaction, "Frais de transaction"
            )

            # Crédit du wallet de la plateforme
            platform_wallet = Wallet.objects.get(is_platform=True)
            TransactionService.credit_wallet(
                platform_wallet, fee_amount, transaction, "Frais collecté"
            )
            
            # Enregistrer le frais dans la transaction
            transaction.fee_applied = fee_amount
            transaction.save(update_fields=['fee_applied'])
            
            # Distribuer les frais entre les acteurs
            FeeService.distribute_fee(transaction, fee_amount, merchant, bank)

        return fee_amount

    @staticmethod
    def distribute_fee(transaction, fee_amount, merchant=None, bank=None):
        """
        Distribue les frais entre les différents acteurs selon les règles définies.
        
        Args:
            transaction: Transaction concernée
            fee_amount: Montant total du frais
            merchant: Marchand concerné (optionnel)
            bank: Banque concernée (optionnel)
            
        Returns:
            list: Liste des objets FeeDistribution créés
        """
        if fee_amount <= 0:
            return []
        
        try:
            # Chercher la règle de distribution
            distribution_rule = FeeDistributionRule.objects.filter(
                transaction_type=transaction.transaction_type,
                is_active=True
            )
            
            # Prioriser les règles spécifiques
            if merchant:
                specific_rule = distribution_rule.filter(merchant=merchant).first()
                if specific_rule:
                    return FeeService._create_distributions(
                        transaction, fee_amount, specific_rule, merchant, bank
                    )
            
            if bank:
                specific_rule = distribution_rule.filter(bank=bank).first()
                if specific_rule:
                    return FeeService._create_distributions(
                        transaction, fee_amount, specific_rule, merchant, bank
                    )
            
            # Règle globale
            global_rule = distribution_rule.filter(
                merchant__isnull=True,
                bank__isnull=True
            ).first()
            
            if global_rule:
                return FeeService._create_distributions(
                    transaction, fee_amount, global_rule, merchant, bank
                )
            
            # Par défaut, tout va au provider
            logger.warning(
                f"No distribution rule found for transaction {transaction.order_id}, "
                f"assigning all fees to provider"
            )
            return [
                FeeDistribution.objects.create(
                    transaction=transaction,
                    actor_type='provider',
                    actor_id=0,  # Provider n'a pas d'ID spécifique
                    amount=fee_amount
                )
            ]
            
        except Exception as e:
            logger.error(f"Error distributing fee for transaction {transaction.order_id}: {e}")
            return []

    @staticmethod
    def _create_distributions(transaction, fee_amount, rule, merchant, bank):
        """
        Crée les entrées de distribution des frais.
        
        Args:
            transaction: Transaction concernée
            fee_amount: Montant total du frais
            rule: Règle de distribution (FeeDistributionRule)
            merchant: Marchand concerné
            bank: Banque concernée
            
        Returns:
            list: Liste des objets FeeDistribution créés
        """
        distributions = []
        
        # Distribution au provider
        if rule.provider_percentage > 0:
            provider_amount = (fee_amount * rule.provider_percentage / Decimal('100')).quantize(Decimal('0.01'))
            if provider_amount > 0:
                distributions.append(
                    FeeDistribution.objects.create(
                        transaction=transaction,
                        actor_type='provider',
                        actor_id=0,
                        amount=provider_amount
                    )
                )
        
        # Distribution à la banque
        if rule.bank_percentage > 0 and bank:
            bank_amount = (fee_amount * rule.bank_percentage / Decimal('100')).quantize(Decimal('0.01'))
            if bank_amount > 0:
                distributions.append(
                    FeeDistribution.objects.create(
                        transaction=transaction,
                        actor_type='bank',
                        actor_id=bank.id,
                        amount=bank_amount
                    )
                )
        
        # Distribution au marchand
        if rule.merchant_percentage > 0 and merchant:
            merchant_amount = (fee_amount * rule.merchant_percentage / Decimal('100')).quantize(Decimal('0.01'))
            if merchant_amount > 0:
                distributions.append(
                    FeeDistribution.objects.create(
                        transaction=transaction,
                        actor_type='merchant',
                        actor_id=merchant.id,
                        amount=merchant_amount
                    )
                )
        
        logger.info(
            f"Fee distribution created for transaction {transaction.order_id}: "
            f"{len(distributions)} distributions totaling {sum(d.amount for d in distributions)}"
        )
        
        return distributions
