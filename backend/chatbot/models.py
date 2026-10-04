"""Chatbot models — reserved for Phase 8 (optional conversation log)."""

from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    """Optional log of chatbot exchanges."""

    class Sender(models.TextChoices):
        USER = "USER", "User"
        BOT = "BOT", "Bot"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        null=True,
        blank=True,
    )
    sender = models.CharField(max_length=10, choices=Sender.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        preview = self.content[:50]
        return f"[{self.sender}] {preview}"
