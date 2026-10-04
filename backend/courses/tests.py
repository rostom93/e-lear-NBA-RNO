from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.models import CustomUser

from .models import Course, Enrollment, Module, Quiz, QuizChoice, QuizQuestion, Tag
from .services import enroll_student


class CourseModelsTests(TestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            password="Teacher123!",
            role=CustomUser.Role.TEACHER,
        )
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            password="Student123!",
            role=CustomUser.Role.STUDENT,
            credit_balance=200,
        )

    def test_course_module_quiz_enrollment_graph(self):
        tag = Tag.objects.create(name="#Python")
        course = Course.objects.create(
            title="Python Basics",
            description="Intro course",
            teacher=self.teacher,
            price_credits=50,
            category="Programming",
        )
        course.tags.add(tag)

        quiz = Quiz.objects.create(title="Python Quiz", passing_score=60)
        question = QuizQuestion.objects.create(quiz=quiz, text="2+2?", order=1)
        QuizChoice.objects.create(question=question, text="4", is_correct=True)
        QuizChoice.objects.create(question=question, text="5", is_correct=False)

        Module.objects.create(
            course=course,
            title="Slides",
            order=1,
            module_type=Module.ModuleType.PDF,
            pdf_url="https://example.com/slides.pdf",
        )
        Module.objects.create(
            course=course,
            title="Lesson video",
            order=2,
            module_type=Module.ModuleType.VIDEO,
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            video_provider=Module.VideoProvider.YOUTUBE,
            transcript="Sample transcript",
        )
        Module.objects.create(
            course=course,
            title="Final quiz",
            order=3,
            module_type=Module.ModuleType.QUIZ,
            quiz=quiz,
        )

        enrollment = Enrollment.objects.create(
            student=self.student,
            course=course,
            credits_spent=50,
        )

        self.assertEqual(course.modules.count(), 3)
        self.assertEqual(str(tag), "#Python")
        self.assertTrue(course.slug)
        self.assertEqual(enrollment.progress_percent, 0)
        self.assertEqual(quiz.questions.count(), 1)
        self.assertEqual(question.choices.filter(is_correct=True).count(), 1)


class CourseAPIPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher = CustomUser.objects.create_user(
            email="teacher@platform.com",
            password="Teacher123!",
            role=CustomUser.Role.TEACHER,
        )
        self.other_teacher = CustomUser.objects.create_user(
            email="other@platform.com",
            password="Teacher123!",
            role=CustomUser.Role.TEACHER,
        )
        self.student = CustomUser.objects.create_user(
            email="guest@gmail.com",
            password="Guest123!",
            role=CustomUser.Role.STUDENT,
            credit_balance=500,
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@platform.com",
            password="Admin123!",
            role=CustomUser.Role.ADMIN,
            is_staff=True,
        )
        self.course = Course.objects.create(
            title="Angular Mastery",
            description="Learn Angular",
            teacher=self.teacher,
            price_credits=100,
            category="Frontend",
            level=Course.Level.BEGINNER,
        )

    def test_public_can_list_active_courses(self):
        response = self.client.get("/api/courses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_student_cannot_create_course(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            "/api/courses/",
            {
                "title": "Hack",
                "description": "Nope",
                "price_credits": 10,
                "level": "BEGINNER",
                "category": "X",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_create_course(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(
            "/api/courses/",
            {
                "title": "Python API",
                "description": "DRF course",
                "price_credits": 80,
                "level": "INTERMEDIATE",
                "category": "Backend",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Python API")

    def test_teacher_cannot_edit_others_course(self):
        self.client.force_authenticate(user=self.other_teacher)
        response = self.client.patch(
            f"/api/courses/{self.course.id}/",
            {"title": "Stolen"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_teacher_can_update_own_course_reusing_quiz(self):
        """Updating modules must allow reattaching the same OneToOne quiz."""
        quiz = Quiz.objects.create(title="Reuse Quiz", passing_score=60)
        Module.objects.create(
            course=self.course,
            title="Quiz module",
            order=1,
            module_type=Module.ModuleType.QUIZ,
            quiz=quiz,
        )
        self.client.force_authenticate(user=self.teacher)
        response = self.client.patch(
            f"/api/courses/{self.course.id}/",
            {
                "title": "Angular Mastery Edited",
                "description": "Learn Angular",
                "price_credits": 120,
                "level": "BEGINNER",
                "category": "Frontend",
                "content_focus": "MIXED",
                "is_active": True,
                "modules": [
                    {
                        "title": "Quiz module updated",
                        "order": 1,
                        "module_type": "QUIZ",
                        "pdf_url": "",
                        "video_url": "",
                        "video_provider": "",
                        "captions_url": "",
                        "transcript": "",
                        "quiz": quiz.id,
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "Angular Mastery Edited")
        self.assertEqual(self.course.modules.count(), 1)
        self.assertEqual(self.course.modules.first().quiz_id, quiz.id)

    def test_module_urls_accept_missing_scheme(self):
        """A teacher pasting `example.com/doc.pdf` must not get a 400."""
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(
            "/api/courses/",
            {
                "title": "Scheme-less URLs",
                "description": "Normalisation check",
                "price_credits": 10,
                "level": "BEGINNER",
                "category": "QA",
                "content_focus": "MIXED",
                "modules": [
                    {
                        "title": "Handbook",
                        "order": 1,
                        "module_type": "PDF",
                        "pdf_url": "example.com/handbook.pdf",
                    },
                    {
                        "title": "Intro",
                        "order": 2,
                        "module_type": "VIDEO",
                        "video_url": "www.youtube.com/watch?v=dQw4w9WgXcQ",
                        "video_provider": "YOUTUBE",
                        "captions_url": "",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        modules = response.data["modules"]
        self.assertEqual(modules[0]["pdf_url"], "https://example.com/handbook.pdf")
        self.assertEqual(
            modules[1]["video_url"], "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        self.assertEqual(modules[1]["captions_url"], "")

    def test_teacher_can_preview_own_inactive_course_with_modules(self):
        """Backs the teacher preview page: inactive own course stays readable."""
        self.course.is_active = False
        self.course.save(update_fields=["is_active"])
        Module.objects.create(
            course=self.course,
            title="Hidden module",
            order=1,
            module_type=Module.ModuleType.PDF,
            pdf_url="https://example.com/hidden.pdf",
        )

        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(f"/api/courses/{self.course.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertFalse(response.data["is_active"])
        self.assertEqual(len(response.data["modules"]), 1)

        self.client.force_authenticate(user=self.student)
        hidden = self.client.get(f"/api/courses/{self.course.id}/")
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_access_admin_stats(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get("/api/admin/stats/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_stats(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("users", response.data)
        self.assertIn("popular_courses", response.data)

    def test_enroll_deducts_credits(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f"/api/courses/{self.course.id}/enroll/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.student.refresh_from_db()
        self.assertEqual(self.student.credit_balance, 400)
        self.assertTrue(
            Enrollment.objects.filter(student=self.student, course=self.course).exists()
        )

    def test_enroll_insufficient_credits(self):
        self.student.credit_balance = 10
        self.student.save(update_fields=["credit_balance"])
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f"/api/courses/{self.course.id}/enroll/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient", str(response.data))

    def test_double_enrollment_rejected(self):
        enroll_student(self.student, self.course)
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f"/api/courses/{self.course.id}/enroll/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already enrolled", str(response.data).lower())
