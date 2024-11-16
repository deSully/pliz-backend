from django.contrib import admin
from .models import Wallet
from .models import Merchant

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'currency')  # Colonnes visibles
    search_fields = ('user__username', 'phone_number', 'currency')  # Recherche
    list_filter = ('currency',)  # Filtres latéraux
    readonly_fields = ('user',)  # Empêche la modification de l'utilisateur lié
    fieldsets = (
        ("Informations du Wallet", {
            'fields': ('user', 'phone_number', 'currency')
        }),
    )
    ordering = ('user',)


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'merchant_code', 'address')  # Colonnes visibles
    search_fields = ('user__username', 'business_name', 'merchant_code')  # Recherche
    list_filter = ('business_name',)  # Filtres par nom commercial
    readonly_fields = ('merchant_code', 'user')  # Champs non modifiables
    fieldsets = (
        ("Informations du Marchand", {
            'fields': ('user', 'business_name', 'merchant_code', 'address')
        }),
    )
