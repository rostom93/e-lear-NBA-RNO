from django.test import TestCase

from users.models import CustomUser

from .models import Course, Enrollment, Module, Quiz, QuizChoice, QuizQuestion
from .services import (
    EnrollmentError,
    enroll_student,
    mark_module_completed,
    submit_quiz,
)


class ProgressCalculationTests(TestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            email="teacher-progress@platform.com",
            password="Teacher123!",
            role=CustomUser.Role.TEACHER,
        )
        self.student = CustomUser.objects.create_user(
            email="student-progress@platform.com",
            password="Student123!",
            role=CustomUser.Role.STUDENT,
            credit_balance=500,
        )
        self.course = Course.objects.create(
            title="Progress Course",
            description="Track completion",
            teacher=self.teacher,
            price_credits=50,
            category="Test",
        )
        self.m1 = Module.objects.create(
            course=self.course,
            title="PDF",
            order=1,
            module_type=Module.ModuleType.PDF,
            pdf_url="https://example.com/a.pdf",
        )
        self.m2 = Module.objects.create(
            course=self.course,
            title="Video",
            order=2,
            module_type=Module.ModuleType.VIDEO,
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            video_provider=Module.VideoProvider.YOUTUBE,
        )
        self.quiz = Quiz.objects.create(title="Progress Quiz", passing_score=50)
        question = QuizQuestion.objects.create(
            quiz=self.quiz, text="Capital of France?", order=1
        )
        self.correct = QuizChoice.objects.create(
            question=question, text="Paris", is_correct=True
        )
        self.wrong = QuizChoice.objects.create(
            question=question, text="Lyon", is_correct=False
        )
        self.m3 = Module.objects.create(
            course=self.course,
            title="Quiz",
            order=3,
            module_type=Module.ModuleType.QUIZ,
            quiz=self.quiz,
        )
        self.enrollment = enroll_student(self.student, self.course)

    def test_progress_starts_at_zero(self):
        self.assertEqual(self.enrollment.progress_percent, 0)

    def test_progress_after_one_module(self):
        mark_module_completed(self.enrollment, self.m1)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.progress_percent, 33)

    def test_progress_after_two_modules(self):
        mark_module_completed(self.enrollment, self.m1)
        mark_module_completed(self.enrollment, self.m2)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.progress_percent, 66)

    def test_progress_full_after_all_modules(self):
        mark_module_completed(self.enrollment, self.m1)
        mark_module_completed(self.enrollment, self.m2)
        mark_module_completed(self.enrollment, self.m3)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.progress_percent, 100)

    def test_passing_quiz_marks_module_and_updates_progress(self):
        mark_module_completed(self.enrollment, self.m1)
        mark_module_completed(self.enrollment, self.m2)
        attempt = submit_quiz(
            self.enrollment,
            self.quiz,
            {str(self.quiz.questions.first().id): self.correct.id},
        )
        self.enrollment.refresh_from_db()
        self.assertTrue(attempt.passed)
        self.assertEqual(attempt.score, 100)
        self.assertEqual(self.enrollment.progress_percent, 100)

    def test_failing_quiz_does_not_complete_module(self):
        attempt = submit_quiz(
            self.enrollment,
            self.quiz,
            {str(self.quiz.questions.first().id): self.wrong.id},
        )
        self.enrollment.refresh_from_db()
        self.assertFalse(attempt.passed)
        self.assertEqual(self.enrollment.progress_percent, 0)


class EnrollmentServiceTests(TestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            email="teacher-enroll@platform.com",
            password="Teacher123!",
            role=CustomUser.Role.TEACHER,
        )
        self.student = CustomUser.objects.create_user(
            email="student-enroll@platform.com",
            password="Student123!",
            role=CustomUser.Role.STUDENT,
            credit_balance=80,
        )
        self.course = Course.objects.create(
            title="Paid Course",
            description="Costs credits",
            teacher=self.teacher,
            price_credits=50,
            category="Test",
        )

    def test_enroll_success(self):
        enrollment = enroll_student(self.student, self.course)
        self.student.refresh_from_db()
        self.assertEqual(enrollment.credits_spent, 50)
        self.assertEqual(self.student.credit_balance, 30)
        self.assertEqual(Enrollment.objects.count(), 1)

    def test_enroll_insufficient_credits(self):
        self.student.credit_balance = 10
        self.student.save(update_fields=["credit_balance"])
        with self.assertRaises(EnrollmentError) as ctx:
            enroll_student(self.student, self.course)
        self.assertIn("Insufficient", str(ctx.exception.detail))
        self.assertEqual(Enrollment.objects.count(), 0)

    def test_enroll_double_rejected(self):
        enroll_student(self.student, self.course)
        with self.assertRaises(EnrollmentError) as ctx:
            enroll_student(self.student, self.course)
        self.assertIn("already enrolled", str(ctx.exception.detail).lower())
        self.assertEqual(Enrollment.objects.count(), 1)
