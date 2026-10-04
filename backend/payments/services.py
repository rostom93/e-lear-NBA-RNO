from django.db import transaction

from users.models import CustomUser

from .models import CreditPack, Transaction


@transaction.atomic
def purchase_credit_pack(
    user: CustomUser,
    pack: CreditPack,
    *,
    force_status: str | None = None,
) -> Transaction:
    """
    Simulate a payment provider.
    Default outcome: SUCCESS. Pass force_status for tests / demos.
    Credits are added only when status is SUCCESS.
    """
    status = force_status or Transaction.Status.SUCCESS
    if status not in Transaction.Status.values:
        status = Transaction.Status.FAILED

    tx = Transaction.objects.create(
        user=user,
        pack=pack,
        credits=pack.credits,
        amount_euros=pack.price_euros,
        status=status,
    )

    if status == Transaction.Status.SUCCESS:
        locked = CustomUser.objects.select_for_update().get(pk=user.pk)
        locked.credit_balance += pack.credits
        locked.save(update_fields=["credit_balance"])

    return tx
