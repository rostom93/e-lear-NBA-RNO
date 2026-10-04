from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "user", "content", "created_at")
    list_filter = ("sender", "created_at")
    search_fields = ("content", "user__email")
