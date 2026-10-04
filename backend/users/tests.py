from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import CustomUser


class CustomUserModelTests(TestCase):
    def test_create_student_with_credits(self):
        user = CustomUser.objects.create_user(
            email="student@example.com",
            password="Test123!",
            role=CustomUser.Role.STUDENT,
            credit_balance=100,
        )
        self.assertEqual(user.email, "student@example.com")
        self.assertTrue(user.is_student)
        self.assertEqual(user.credit_balance, 100)
        self.assertTrue(user.check_password("Test123!"))

    def test_create_superuser_is_admin(self):
        admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="Admin123!",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, CustomUser.Role.ADMIN)


class JWTAuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student = CustomUser.objects.create_user(
            email="guest@gmail.com",
            password="Guest123!",
            role=CustomUser.Role.STUDENT,
            credit_balance=500,
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@platform.com",
            password="Teacher123!",
            role=CustomUser.Role.TEACHER,
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@platform.com",
            password="Admin123!",
            role=CustomUser.Role.ADMIN,
            is_staff=True,
        )

    def test_obtain_jwt_with_email(self):
        response = self.client.post(
            "/api/auth/token/",
            {"email": "guest@gmail.com", "password": "Guest123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], "STUDENT")

    def test_me_requires_auth(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_token(self):
        token = self.client.post(
            "/api/auth/token/",
            {"email": "guest@gmail.com", "password": "Guest123!"},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "guest@gmail.com")

    def test_student_cannot_list_users(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 3)

    def test_register_creates_student(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new@student.com",
                "password": "NewStudent123!",
                "first_name": "New",
                "last_name": "Student",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(email="new@student.com")
        self.assertEqual(user.role, CustomUser.Role.STUDENT)
