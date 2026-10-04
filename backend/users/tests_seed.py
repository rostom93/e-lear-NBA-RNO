from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from courses.models import Course, Module, Tag
from payments.models import CreditPack, Transaction
from users.models import CustomUser


class SeedDataCommandTests(TestCase):
    def test_seed_creates_expected_demo_data(self):
        out = StringIO()
        call_command("seed_data", stdout=out)

        admin = CustomUser.objects.get(email="admin@platform.com")
        teacher = CustomUser.objects.get(email="teacher@platform.com")
        guest = CustomUser.objects.get(email="guest@gmail.com")

        self.assertEqual(admin.role, CustomUser.Role.ADMIN)
        self.assertTrue(admin.check_password("Admin123!"))
        self.assertEqual(teacher.role, CustomUser.Role.TEACHER)
        self.assertTrue(teacher.check_password("Teacher123!"))
        self.assertEqual(guest.role, CustomUser.Role.STUDENT)
        self.assertEqual(guest.credit_balance, 500)
        self.assertTrue(guest.check_password("Guest123!"))

        self.assertEqual(Tag.objects.filter(name__in=["#Angular", "#Python", "#AI"]).count(), 3)
        self.assertEqual(Course.objects.filter(is_active=True).count(), 3)
        self.assertEqual(CreditPack.objects.filter(is_active=True).count(), 3)

        for slug in (
            "angular-fundamentals",
            "python-for-beginners",
            "introduction-to-ai",
        ):
            course = Course.objects.get(slug=slug)
            modules = list(course.modules.order_by("order"))
            self.assertEqual(len(modules), 3)
            self.assertEqual(modules[0].module_type, Module.ModuleType.PDF)
            self.assertEqual(modules[1].module_type, Module.ModuleType.VIDEO)
            self.assertEqual(modules[2].module_type, Module.ModuleType.QUIZ)
            self.assertIsNotNone(modules[2].quiz)
            self.assertGreaterEqual(modules[2].quiz.questions.count(), 2)
            self.assertTrue(modules[1].transcript)

        self.assertGreaterEqual(
            Transaction.objects.filter(status=Transaction.Status.SUCCESS).count(),
            2,
        )

    def test_seed_is_idempotent(self):
        call_command("seed_data", stdout=StringIO())
        counts = {
            "users": CustomUser.objects.count(),
            "courses": Course.objects.count(),
            "modules": Module.objects.count(),
            "packs": CreditPack.objects.count(),
            "tags": Tag.objects.count(),
            "transactions": Transaction.objects.count(),
        }

        call_command("seed_data", stdout=StringIO())

        self.assertEqual(CustomUser.objects.count(), counts["users"])
        self.assertEqual(Course.objects.count(), counts["courses"])
        self.assertEqual(Module.objects.count(), counts["modules"])
        self.assertEqual(CreditPack.objects.count(), counts["packs"])
        self.assertEqual(Tag.objects.count(), counts["tags"])
        self.assertEqual(Transaction.objects.count(), counts["transactions"])

        guest = CustomUser.objects.get(email="guest@gmail.com")
        self.assertEqual(guest.credit_balance, 500)
