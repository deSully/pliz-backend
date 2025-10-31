from django.core.management.base import BaseCommand
from django.db import transaction
from transaction.models import Transaction, TransactionStatusCheck
from transaction.partners.factory import PartnerGatewayFactory


class Command(BaseCommand):
    """
    Commande Django pour vérifier et mettre à jour les transactions en attente.
    
    Cette commande interroge les partenaires de paiement pour obtenir le statut actuel
    des transactions qui sont en attente (PENDING) et met à jour les modèles
    TransactionStatusCheck et Transaction en conséquence.
    
    Usage:
        python manage.py check_pending_transactions
    """
    help = "Check and update pending transactions"

    def handle(self, *args, **kwargs):
        """
        Point d'entrée principal de la commande.
        
        Récupère toutes les transactions en attente, vérifie leur statut auprès
        des partenaires et met à jour les enregistrements si le statut a changé.
        """
        pending_checks = TransactionStatusCheck.objects.filter(status="PENDING")
        self.stdout.write(f"Found {pending_checks.count()} pending transactions")

        for check in pending_checks:
            new_status = self.get_status_from_partner(
                check.partner, check.external_reference
            )

            if new_status and new_status != check.status:
                self.stdout.write(
                    f"Updating {check.external_reference} to {new_status}"
                )
                with transaction.atomic():
                    check.status = new_status
                    check.save(update_fields=["status", "last_checked_at"])

                    Transaction.objects.filter(order_id=check.order_id).update(
                        status=new_status.upper()
                    )

    def get_status_from_partner(self, partner, external_reference):
        """
        Interroge le partenaire de paiement pour obtenir le statut d'une transaction.
        
        Args:
            partner (str): Le nom du partenaire de paiement (ex: "WAVE", "ORANGE_MONEY")
            external_reference (str): La référence externe de la transaction chez le partenaire
            
        Returns:
            str | None: Le nouveau statut de la transaction, ou None en cas d'erreur
        """
        try:
            gateway = PartnerGatewayFactory(partner)
            status = gateway.get_transaction_status(external_reference)
            return status
        except Exception as e:
            self.stdout.write(f"Error checking {external_reference}: {e}")
            return None