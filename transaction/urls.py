from django.urls import path
from transaction.views.send_money import SendMoneyView
from transaction.views.merchant_payment import MerchantPaymentView
from transaction.views.merchant_initiated_payment import MerchantInitiatedPaymentView

from transaction.views.history import TransactionHistoryView
from transaction.views.topup import TopUpView
from transaction.views.balance import BalanceView
from transaction.views.transaction_detail import TransactionDetailView

urlpatterns = [
    path(
        "send-money/", SendMoneyView.as_view(), name="send-money"
    ),  # URL pour envoyer de l'argent
    path(
        "merchant-payment/", MerchantPaymentView.as_view(), name="merchant-payment"
    ),  # URL pour les paiements marchands (client paie le marchand)
    path(
        "merchant/scan-payment/", MerchantInitiatedPaymentView.as_view(), name="merchant-scan-payment"
    ),  # URL pour les paiements initiés par le marchand (scan QR code)
    path(
        "history/", TransactionHistoryView.as_view(), name="transaction-history"
    ),  # URL pour l'historique des transactions
    path(
        "detail/<str:order_id>/", TransactionDetailView.as_view(), name="transaction-detail"
    ),  # URL pour le détail d'une transaction
    path("wallet/topup/", TopUpView.as_view(), name="wallet-topup"),

    # URL pour demander le solde du portefeuille
    path("wallet/balance/", BalanceView.as_view(), name="wallet-balance"),
]
