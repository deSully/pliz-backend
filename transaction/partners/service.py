from django.db import transaction as db_transaction
from transaction.services.transaction import TransactionService
from transaction.errors import PaymentProcessingError
from transaction.models import TransactionType
from actor.models import RIB
from actor.models import Wallet


class BankTopUpService:
    @staticmethod
    def process_topup(user, rib_uuid, amount):
        """
        Recharge le portefeuille d'un utilisateur à partir d'un compte bancaire (RIB).
        """

        try:
            with db_transaction.atomic():
                # 1. Récupérer le RIB et vérifier qu'il appartient à l'utilisateur
                try:
                    rib = RIB.objects.get(uuid=rib_uuid, user=user)
                except RIB.DoesNotExist:
                    raise PaymentProcessingError(
                        "Le compte bancaire spécifié est introuvable ou ne vous appartient pas."
                    )

                # 2. Récupérer le wallet de l'utilisateur
                wallet = Wallet.objects.get(user=user)

                # 3. Créer une transaction en attente
                description = f"Rechargement depuis {rib.banque} - {rib.numero_compte}"
                transaction = TransactionService.create_pending_transaction(
                    sender=None,  # pas de wallet émetteur car externe
                    receiver=wallet,
                    transaction_type=TransactionType.TOPUP.value,
                    amount=amount,
                    description=description,
                )

                # 4. (Optionnel) Appel à une API bancaire si c'était connecté
                # Exemple :
                # bank_gateway = BankGatewayFactory.get_gateway(rib.banque)
                # bank_gateway.debit(rib, amount)

                # 5. Créditer le wallet
                TransactionService.credit_wallet(
                    wallet, amount, transaction, description
                )

                # 6. Marquer la transaction comme réussie
                TransactionService.update_transaction_status(transaction, "completed")

                return transaction

        except Exception as e:
            raise PaymentProcessingError(f"Échec du rechargement : {str(e)}")
