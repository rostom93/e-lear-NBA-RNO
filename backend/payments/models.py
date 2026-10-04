from django.conf import settings
from django.db import models


class CreditPack(models.Model):
    """Purchasable credit pack (simulated payment)."""

    name = models.CharField(max_length=100)
    credits = models.PositiveIntegerField()
    price_euros = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["credits"]

    def __str__(self) -> str:
        return f"{self.name} ({self.credits} credits — {self.price_euros}€)"


class Transaction(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        PENDING = "PENDING", "Pending"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    pack = models.ForeignKey(
        CreditPack,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    credits = models.PositiveIntegerField()
    amount_euros = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} — {self.credits} credits ({self.status})"
