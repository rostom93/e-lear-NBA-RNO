from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import CustomUser
from users.permissions import IsAdminRole

from .models import CreditPack, Transaction
from .serializers import CreditPackSerializer, PurchaseSerializer, TransactionSerializer
from .services import purchase_credit_pack


class CreditPackViewSet(viewsets.ModelViewSet):
    serializer_class = CreditPackSerializer

    def get_queryset(self):
        qs = CreditPack.objects.all()
        if self.request.user.is_authenticated and self.request.user.role == CustomUser.Role.ADMIN:
            return qs
        return qs.filter(is_active=True)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAdminRole()]


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Transaction.objects.select_related("user", "pack")
        if user.role == CustomUser.Role.ADMIN:
            return qs
        return qs.filter(user=user)

    @action(detail=False, methods=["post"], url_path="purchase")
    def purchase(self, request):
        if request.user.role != CustomUser.Role.STUDENT and request.user.role != CustomUser.Role.ADMIN:
            # Teachers can also buy credits if needed; allow STUDENT primarily
            if request.user.role == CustomUser.Role.TEACHER:
                pass

        serializer = PurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            pack = CreditPack.objects.get(
                pk=serializer.validated_data["pack_id"],
                is_active=True,
            )
        except CreditPack.DoesNotExist:
            return Response(
                {"detail": "Credit pack not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        tx = purchase_credit_pack(
            request.user,
            pack,
            force_status=serializer.validated_data.get("simulate_status"),
        )
        request.user.refresh_from_db()
        return Response(
            {
                "transaction": TransactionSerializer(tx).data,
                "credit_balance": request.user.credit_balance,
            },
            status=status.HTTP_201_CREATED,
        )
