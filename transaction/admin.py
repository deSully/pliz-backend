from django.contrib import admin
from .models import Transaction, Fee

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'sender', 'receiver', 'amount', 'status', 'timestamp')  # Colonnes affichées
    search_fields = ('sender__username', 'receiver__username', 'transaction_type', 'status')   # Recherche
    list_filter = ('transaction_type', 'status', 'timestamp')                                  # Filtres latéraux
    readonly_fields = ('timestamp',)                                                          # Champs en lecture seule
    fieldsets = (                                                                              # Organisation des champs
        ("Détails de la transaction", {
            'fields': ('transaction_type', 'amount', 'status', 'description')
        }),
        ("Participants", {
            'fields': ('sender', 'receiver')
        }),
        ("Dates", {
            'fields': ('timestamp',)
        }),
    )
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    list_per_page = 20
    list_max_show_all = 100

    actions = ['mark_as_completed', 'mark_as_failed']

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} transactions marquées comme réussies.")
    mark_as_completed.short_description = "Marquer comme réussie"

    def mark_as_failed(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, f"{queryset.count()} transactions marquées comme échouées.")
    mark_as_failed.short_description = "Marquer comme échouée"


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_type', 
        'merchant', 
        'bank', 
        'percentage', 
        'fixed_amount', 
        'is_active', 
        'get_fee_display'
    )
    list_filter = ('transaction_type', 'merchant', 'bank', 'is_active')
    search_fields = ('merchant__name', 'bank__name', 'transaction_type')
    ordering = ('-is_active', 'transaction_type')

    def get_fee_display(self, obj):
        # Calcul du total des frais en fonction du pourcentage et du montant fixe
        if obj.percentage and obj.fixed_amount:
            return f"{obj.percentage}% + {obj.fixed_amount} CFA"
        elif obj.percentage:
            return f"{obj.percentage}%"
        elif obj.fixed_amount:
            return f"{obj.fixed_amount} CFA"
        return "Aucun frais"

    get_fee_display.short_description = "Frais appliqués"

    def save_model(self, request, obj, form, change):
        # Vous pouvez ajouter de la logique ici, comme des calculs ou des ajustements
        super().save_model(request, obj, form, change)