from django.contrib import admin
from .models import Transaction, Fee, TariffGrid, WalletBalanceHistory


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_type",
        "sender",
        "receiver",
        "amount",
        "status",
        "timestamp",
        "description"
    )  # Colonnes affichées
    search_fields = (
        "sender__username",
        "receiver__username",
        "transaction_type",
        "status",
    )  # Recherche
    list_filter = ("transaction_type", "status", "timestamp")  # Filtres latéraux
    readonly_fields = ("timestamp",)  # Champs en lecture seule
    fieldsets = (  # Organisation des champs
        (
            "Détails de la transaction",
            {"fields": ("transaction_type", "amount", "status", "description")},
        ),
        ("Participants", {"fields": ("sender", "receiver")}),
        ("Dates", {"fields": ("timestamp",)}),
    )
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"
    list_per_page = 20
    list_max_show_all = 100

    actions = ["mark_as_completed", "mark_as_failed"]

    def mark_as_completed(self, request, queryset):
        queryset.update(status="completed")
        self.message_user(
            request, f"{queryset.count()} transactions marquées comme réussies."
        )

    mark_as_completed.short_description = "Marquer comme réussie"

    def mark_as_failed(self, request, queryset):
        queryset.update(status="failed")
        self.message_user(
            request, f"{queryset.count()} transactions marquées comme échouées."
        )

    mark_as_failed.short_description = "Marquer comme échouée"


class FeeInline(admin.TabularInline):
    model = Fee
    extra = 1
    fields = (
        "transaction_type",
        "min_amount",
        "max_amount",
        "percentage",
        "fixed_amount",
        "merchant",
        "bank",
        "is_active",
    )
    autocomplete_fields = ["merchant", "bank"]
    show_change_link = True


@admin.register(TariffGrid)
class TariffGridAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = [FeeInline]


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_type",
        "min_amount",
        "max_amount",
        "percentage",
        "fixed_amount",
        "merchant",
        "bank",
        "tariff_grid",
        "is_active",
    )
    list_filter = (
        "transaction_type",
        "is_active",
        "tariff_grid",
    )
    search_fields = (
        "merchant__name",
        "bank__name",
    )
    autocomplete_fields = ["merchant", "bank", "tariff_grid"]




@admin.register(WalletBalanceHistory)
class WalletBalanceHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "wallet_user",
        "balance_before",
        "balance_after",
        "transaction_type",
        "timestamp",
    )
    list_filter = ("transaction_type", "timestamp")
    search_fields = ("wallet__user__username", "description", "transaction__id")
    # readonly_fields = (
    #     "wallet",
    #     "balance_before",
    #     "balance_after",
    #     "transaction",
    #     "transaction_type",
    #     "timestamp",
    #     "description",
    # )
    ordering = ("-timestamp",)

    def wallet_user(self, obj):
        return obj.wallet.user.username

    wallet_user.short_description = "Utilisateur du Wallet"
