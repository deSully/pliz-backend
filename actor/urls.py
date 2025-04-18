from django.urls import path
from actor.views.check_otp import CheckOTPView
from actor.views.login import LoginView
from actor.views.rib import RIBListCreateView, RIBDeleteView
from actor.views.send_otp import SendOTPView
from actor.views.registration import UserRegistrationView

urlpatterns = [
    path("auth/register/", UserRegistrationView.as_view(), name="user-registration"),
    path("auth/send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("auth/check-otp/", CheckOTPView.as_view(), name="check-otp"),
    path("auth/login/", LoginView.as_view(), name="login"),

    # RIB endpoints
    path("ribs/", RIBListCreateView.as_view(), name="rib-list-create"),
    path("ribs/<int:pk>/delete/", RIBDeleteView.as_view(), name="rib-delete"),
]
