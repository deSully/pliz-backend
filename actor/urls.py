# myapp/urls.py
from django.urls import path
from .views.registration import UserRegistrationView
from .views.account_activation import UserAccountActivationView
from .views.send_otp import SendOTPView

urlpatterns = [
    path('auth/register', UserRegistrationView.as_view(), name='user-registration'),
    path('auth/activate-account/', UserAccountActivationView.as_view(), name='user-account-activation'),

    path('auth/send-otp/', SendOTPView.as_view(), name='send-otp'),
]
