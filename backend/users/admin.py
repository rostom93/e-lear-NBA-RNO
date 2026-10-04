from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "email",
        "username",
        "role",
        "credit_balance",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = UserAdmin.fieldsets + (
        ("Platform", {"fields": ("role", "credit_balance")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Platform", {"fields": ("email", "role", "credit_balance")}),
    )
