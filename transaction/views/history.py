from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from actor.models import Wallet
from transaction.serializers import TransactionSerializer
from transaction.models import Transaction

class TransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Récupérer l'utilisateur connecté
        user = self.request.user
        wallet = Wallet.objects.get(user=user)
        # Récupérer toutes les transactions envoyées ou reçues par l'utilisateur
        transactions = Transaction.objects.filter(sender=wallet) | Transaction.objects.filter(receiver=wallet)
        return transactions.order_by('-timestamp')
