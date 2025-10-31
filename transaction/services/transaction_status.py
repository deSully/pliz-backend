from transaction.models import TransactionStatusCheck


class TransactionStatusService:
    @staticmethod
    def register(order_id, external_reference, status, transaction_type, partner):
        obj, _ = TransactionStatusCheck.objects.update_or_create(
            external_reference=external_reference,
            defaults={
                "order_id": order_id,
                "status": status,
                "transaction_type": transaction_type,
                "partner": partner,
            },
        )
        return obj
