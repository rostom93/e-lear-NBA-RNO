from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from users.models import CustomUser

from .models import Course, Enrollment, Module, ModuleProgress, Quiz, QuizAttempt


class EnrollmentError(ValidationError):
    """Raised when enrollment cannot proceed."""


@transaction.atomic
def enroll_student(student: CustomUser, course: Course) -> Enrollment:
    if not course.is_active:
        raise EnrollmentError({"detail": "This course is not available."})

    if Enrollment.objects.filter(student=student, course=course).exists():
        raise EnrollmentError({"detail": "You are already enrolled in this course."})

    locked_student = CustomUser.objects.select_for_update().get(pk=student.pk)
    price = course.price_credits
    if locked_student.credit_balance < price:
        raise EnrollmentError(
            {
                "detail": "Insufficient credits.",
                "required": price,
                "balance": locked_student.credit_balance,
            }
        )

    locked_student.credit_balance -= price
    locked_student.save(update_fields=["credit_balance"])

    enrollment = Enrollment.objects.create(
        student=locked_student,
        course=course,
        credits_spent=price,
        progress_percent=0,
    )
    return enrollment


@transaction.atomic
def mark_module_completed(enrollment: Enrollment, module: Module) -> ModuleProgress:
    if module.course_id != enrollment.course_id:
        raise ValidationError({"detail": "Module does not belong to this course."})

    progress, _ = ModuleProgress.objects.get_or_create(
        enrollment=enrollment,
        module=module,
    )
    if not progress.completed:
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save(update_fields=["completed", "completed_at"])
        enrollment.recalculate_progress()
    return progress


@transaction.atomic
def submit_quiz(
    enrollment: Enrollment,
    quiz: Quiz,
    answers: dict,
) -> QuizAttempt:
    module = getattr(quiz, "module", None)
    if module is None or module.course_id != enrollment.course_id:
        raise ValidationError({"detail": "Quiz is not part of this enrollment's course."})

    questions = list(quiz.questions.prefetch_related("choices"))
    if not questions:
        raise ValidationError({"detail": "Quiz has no questions."})

    correct = 0
    normalized: dict[str, int] = {}
    for question in questions:
        raw = answers.get(str(question.id), answers.get(question.id))
        if raw is None:
            continue
        choice_id = int(raw)
        normalized[str(question.id)] = choice_id
        if question.choices.filter(id=choice_id, is_correct=True).exists():
            correct += 1

    score = int((correct / len(questions)) * 100)
    passed = score >= quiz.passing_score
    attempt = QuizAttempt.objects.create(
        enrollment=enrollment,
        quiz=quiz,
        score=score,
        passed=passed,
        answers=normalized,
    )

    if passed:
        mark_module_completed(enrollment, module)

    return attempt
