# myapp/urls.py
from django.urls import path
from .views.registration import UserRegistrationView
from .views.account_activation import UserAccountActivationView

urlpatterns = [
    path('auth/register', UserRegistrationView.as_view(), name='user-registration'),
    path('auth/activate-account/', UserAccountActivationView.as_view(), name='user-account-activation'),
]
