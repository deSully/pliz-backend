from django.contrib import admin
from .models import Wallet
from .models import Merchant
from .models import RIB
from .models import Bank
from .models import Country
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "currency")  # Colonnes visibles
    search_fields = ("user__username", "phone_number", "currency")  # Recherche
    list_filter = ("currency",)  # Filtres latéraux
    readonly_fields = ("user",)  # Empêche la modification de l'utilisateur lié
    fieldsets = (
        ("Informations du Wallet", {"fields": ("user", "phone_number", "currency")}),
    )
    ordering = ("user",)


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = (
        "wallet",
        "business_name",
        "merchant_code",
        "address",
    )  # Colonnes visibles
    search_fields = (
        "wallet__user__username",
        "business_name",
        "merchant_code",
    )  # Recherche
    list_filter = ("business_name",)  # Filtres par nom commercial
    readonly_fields = ("merchant_code", "wallet")  # Champs non modifiables
    fieldsets = (
        (
            "Informations du Marchand",
            {"fields": ("wallet", "business_name", "merchant_code", "address")},
        ),
    )


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    list_filter = ("country",)
    search_fields = ("name",)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name",)


@admin.register(RIB)
class RIBAdmin(admin.ModelAdmin):
    list_display = ("titulaire", "banque", "numero_compte", "user", "created_at")
    search_fields = ("titulaire", "banque", "numero_compte")
list_filter = ("banque", "created_at")



CustomUser = get_user_model()

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_staff", "is_active", "is_superuser")