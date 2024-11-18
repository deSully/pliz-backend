from django.urls import path
from transaction.views.send_money import SendMoneyView
from transaction.views.merchant_payment import MerchantPaymentView

urlpatterns = [
    path('send-money/', SendMoneyView.as_view(), name='send-money'),  # URL pour envoyer de l'argent
    path('merchant-payment/', MerchantPaymentView.as_view(), name='merchant-payment'),  # URL pour les paiements marchands
]
