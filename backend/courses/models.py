from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class Tag(models.Model):
    """Course tag, e.g. #Angular, #Python, #AI."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name.lstrip("#"))
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name if self.name.startswith("#") else f"#{self.name}"


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"

    class ContentFocus(models.TextChoices):
        MIXED = "MIXED", "Mixed"
        VIDEO = "VIDEO", "Video"
        PDF = "PDF", "PDF"
        QUIZ = "QUIZ", "Quiz"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="taught_courses",
        limit_choices_to={"role": "TEACHER"},
    )
    price_credits = models.PositiveIntegerField(default=0)
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.BEGINNER,
    )
    category = models.CharField(max_length=100)
    content_focus = models.CharField(
        max_length=20,
        choices=ContentFocus.choices,
        default=ContentFocus.MIXED,
    )
    tags = models.ManyToManyField(Tag, related_name="courses", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class Quiz(models.Model):
    """Standalone quiz that can be attached to a module."""

    title = models.CharField(max_length=200)
    passing_score = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum percentage required to pass.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.quiz.title} — Q{self.order}"


class QuizChoice(models.Model):
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        marker = "✓" if self.is_correct else "✗"
        return f"{marker} {self.text[:60]}"


class Module(models.Model):
    class ModuleType(models.TextChoices):
        PDF = "PDF", "PDF"
        VIDEO = "VIDEO", "Video"
        QUIZ = "QUIZ", "Quiz"

    class VideoProvider(models.TextChoices):
        YOUTUBE = "YOUTUBE", "YouTube"
        VIMEO = "VIMEO", "Vimeo"
        OTHER = "OTHER", "Other"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    module_type = models.CharField(max_length=10, choices=ModuleType.choices)
    pdf_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)
    video_provider = models.CharField(
        max_length=20,
        choices=VideoProvider.choices,
        blank=True,
    )
    # Accessibility: captions & transcriptions
    captions_url = models.URLField(blank=True)
    transcript = models.TextField(blank=True)
    quiz = models.OneToOneField(
        Quiz,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="module",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("course", "order")]

    def __str__(self) -> str:
        return f"{self.course.title} — {self.order}. {self.title}"


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    credits_spent = models.PositiveIntegerField(default=0)
    progress_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("student", "course")]
        ordering = ["-enrolled_at"]

    def __str__(self) -> str:
        return f"{self.student.email} → {self.course.title}"

    def recalculate_progress(self) -> int:
        """Recompute completion percentage from module progress rows."""
        total = self.course.modules.count()
        if total == 0:
            self.progress_percent = 0
        else:
            completed = self.module_progress.filter(completed=True).count()
            self.progress_percent = int((completed / total) * 100)
        self.save(update_fields=["progress_percent"])
        return self.progress_percent


class ModuleProgress(models.Model):
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="module_progress",
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="progress_entries",
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("enrollment", "module")]
        verbose_name_plural = "Module progress"

    def __str__(self) -> str:
        status = "done" if self.completed else "pending"
        return f"{self.enrollment} / {self.module.title} ({status})"


class QuizAttempt(models.Model):
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    passed = models.BooleanField(default=False)
    answers = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.enrollment.student.email} — {self.quiz.title}: {self.score}%"
