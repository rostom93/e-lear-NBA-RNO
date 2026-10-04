from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.models import CustomUser

from .models import CreditPack, Transaction
from .services import purchase_credit_pack


class PaymentModelsTests(TestCase):
    def test_transaction_statuses(self):
        user = CustomUser.objects.create_user(
            email="buyer@example.com",
            password="Buyer123!",
            role=CustomUser.Role.STUDENT,
        )
        pack = CreditPack.objects.create(
            name="Starter",
            credits=100,
            price_euros=Decimal("9.99"),
        )
        tx = Transaction.objects.create(
            user=user,
            pack=pack,
            credits=pack.credits,
            amount_euros=pack.price_euros,
            status=Transaction.Status.SUCCESS,
        )
        self.assertEqual(tx.status, Transaction.Status.SUCCESS)
        self.assertEqual(tx.credits, 100)


class PaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student = CustomUser.objects.create_user(
            email="guest@gmail.com",
            password="Guest123!",
            role=CustomUser.Role.STUDENT,
            credit_balance=0,
        )
        self.pack = CreditPack.objects.create(
            name="Pro",
            credits=200,
            price_euros=Decimal("19.99"),
        )

    def test_purchase_success_adds_credits(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            "/api/transactions/purchase/",
            {"pack_id": self.pack.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["credit_balance"], 200)
        self.assertEqual(response.data["transaction"]["status"], "SUCCESS")

    def test_failed_purchase_does_not_add_credits(self):
        purchase_credit_pack(
            self.student,
            self.pack,
            force_status=Transaction.Status.FAILED,
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.credit_balance, 0)
