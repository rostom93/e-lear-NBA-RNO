from rest_framework import serializers

from .models import CreditPack, Transaction


class CreditPackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditPack
        fields = ("id", "name", "credits", "price_euros", "is_active")


class TransactionSerializer(serializers.ModelSerializer):
    pack_name = serializers.CharField(source="pack.name", read_only=True, default=None)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "user",
            "user_email",
            "pack",
            "pack_name",
            "credits",
            "amount_euros",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class PurchaseSerializer(serializers.Serializer):
    pack_id = serializers.IntegerField()
    # Optional simulation knob: SUCCESS | PENDING | FAILED
    simulate_status = serializers.ChoiceField(
        choices=Transaction.Status.choices,
        required=False,
    )
