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
    list_display = ("username", "email", "uuid", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name", "uuid")
    list_filter = ("is_staff", "is_active", "is_superuser")
    readonly_fields = ("uuid",)  # UUID en lecture seule dans le formulaire
    
    # Ajouter UUID dans les fieldsets pour qu'il apparaisse dans le détail
    fieldsets = UserAdmin.fieldsets + (
        ("Identifiant unique", {"fields": ("uuid",)}),
    )