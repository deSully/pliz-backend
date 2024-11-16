# myapp/urls.py
from django.urls import path
from .views import UserRegistrationView

urlpatterns = [
    path('auth/', UserRegistrationView.as_view(), name='user-registration'),
]