from django.contrib import admin

from .models import CreditPack, Transaction


@admin.register(CreditPack)
class CreditPackAdmin(admin.ModelAdmin):
    list_display = ("name", "credits", "price_euros", "is_active")
    list_filter = ("is_active",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "pack",
        "credits",
        "amount_euros",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("created_at", "updated_at")
