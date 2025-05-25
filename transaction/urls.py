from django.urls import path
from transaction.views.send_money import SendMoneyView
from transaction.views.merchant_payment import MerchantPaymentView

from transaction.views.history import TransactionHistoryView
from transaction.views.topup import TopUpView
from transaction.views.balance import BalanceView

urlpatterns = [
    path(
        "send-money/", SendMoneyView.as_view(), name="send-money"
    ),  # URL pour envoyer de l'argent
    path(
        "merchant-payment/", MerchantPaymentView.as_view(), name="merchant-payment"
    ),  # URL pour les paiements marchands
    path(
        "history/", TransactionHistoryView.as_view(), name="transaction-history"
    ),  # URL pour l'historique des transactions
    path("wallet/topup/", TopUpView.as_view(), name="wallet-topup"),

    # URL pour demander le solde du portefeuille
    path("wallet/balance/", BalanceView.as_view(), name="wallet-balance"),
]
