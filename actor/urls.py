# urls.py
from django.urls import path

from .views.check_otp import CheckOTPView
from .views.registration import UserRegistrationView
from .views.account_activation import UserAccountActivationView
from .views.send_otp import SendOTPView
from .views.send_login_otp import SendLoginOTPView
from.views.login import LoginView

urlpatterns = [
    path("auth/register/", UserRegistrationView.as_view(), name="user-registration"),
    path(
        "auth/activate-account/",
        UserAccountActivationView.as_view(),
        name="user-account-activation",
    ),
    path("auth/send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("auth/check-otp/", CheckOTPView.as_view(), name="check-otp"),

    path("auth/send-login-otp/", SendLoginOTPView.as_view(), name="send-login-otp"),

    path("auth/login/", LoginView.as_view(), name="login"),
    
]
