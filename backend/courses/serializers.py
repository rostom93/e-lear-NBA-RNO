from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Course,
    Enrollment,
    Module,
    ModuleProgress,
    Quiz,
    QuizAttempt,
    QuizChoice,
    QuizQuestion,
    Tag,
)

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class QuizChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizChoice
        fields = ("id", "text")


class QuizChoiceAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizChoice
        fields = ("id", "text", "is_correct")


class QuizQuestionPublicSerializer(serializers.ModelSerializer):
    choices = QuizChoicePublicSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ("id", "text", "order", "choices")


class QuizQuestionWriteSerializer(serializers.ModelSerializer):
    choices = QuizChoiceAdminSerializer(many=True)

    class Meta:
        model = QuizQuestion
        fields = ("id", "text", "order", "choices")


class QuizPublicSerializer(serializers.ModelSerializer):
    questions = QuizQuestionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ("id", "title", "passing_score", "questions")


class QuizWriteSerializer(serializers.ModelSerializer):
    questions = QuizQuestionWriteSerializer(many=True, required=False)

    class Meta:
        model = Quiz
        fields = ("id", "title", "passing_score", "questions")

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        quiz = Quiz.objects.create(**validated_data)
        self._save_questions(quiz, questions_data)
        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data is not None:
            instance.questions.all().delete()
            self._save_questions(instance, questions_data)
        return instance

    def _save_questions(self, quiz, questions_data):
        for q_data in questions_data:
            choices = q_data.pop("choices", [])
            question = QuizQuestion.objects.create(quiz=quiz, **q_data)
            for c_data in choices:
                QuizChoice.objects.create(question=question, **c_data)


class ModuleSerializer(serializers.ModelSerializer):
    quiz = QuizPublicSerializer(read_only=True)
    quiz_id = serializers.PrimaryKeyRelatedField(
        queryset=Quiz.objects.all(),
        source="quiz",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Module
        fields = (
            "id",
            "title",
            "order",
            "module_type",
            "pdf_url",
            "video_url",
            "video_provider",
            "captions_url",
            "transcript",
            "quiz",
            "quiz_id",
        )


class NormalizedURLField(serializers.URLField):
    """URL field that accepts scheme-less input such as `example.com/doc.pdf`.

    The scheme has to be added before URLField's own validators run, so it cannot
    be done in a `validate_<field>` hook.
    """

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = data.strip()
            if data and "://" not in data:
                data = f"https://{data}"
        return super().to_internal_value(data)


class ModuleWriteSerializer(serializers.ModelSerializer):
    # Explicit PK field: ModelSerializer would attach a UniqueValidator for the
    # OneToOne quiz link, which blocks course updates that reuse the same quiz
    # while the previous module row still exists during validation.
    quiz = serializers.PrimaryKeyRelatedField(
        queryset=Quiz.objects.all(),
        allow_null=True,
        required=False,
    )
    pdf_url = NormalizedURLField(required=False, allow_blank=True)
    video_url = NormalizedURLField(required=False, allow_blank=True)
    captions_url = NormalizedURLField(required=False, allow_blank=True)
    video_provider = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Module
        fields = (
            "id",
            "title",
            "order",
            "module_type",
            "pdf_url",
            "video_url",
            "video_provider",
            "captions_url",
            "transcript",
            "quiz",
        )

    def validate_video_provider(self, value):
        value = (value or "").strip()
        if not value:
            return ""
        allowed = {choice for choice, _ in Module.VideoProvider.choices}
        if value not in allowed:
            raise serializers.ValidationError(
                f"Invalid provider. Choose one of {sorted(allowed)}."
            )
        return value


class CourseListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    teacher_email = serializers.EmailField(source="teacher.email", read_only=True)
    modules_count = serializers.IntegerField(source="modules.count", read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "teacher",
            "teacher_email",
            "price_credits",
            "level",
            "category",
            "content_focus",
            "tags",
            "is_active",
            "modules_count",
            "created_at",
        )


class CourseDetailSerializer(CourseListSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ("modules", "updated_at")


class CourseWriteSerializer(serializers.ModelSerializer):
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        source="tags",
        required=False,
    )
    modules = ModuleWriteSerializer(many=True, required=False)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "description",
            "price_credits",
            "level",
            "category",
            "content_focus",
            "tag_ids",
            "is_active",
            "modules",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        modules_data = validated_data.pop("modules", [])
        tags = validated_data.pop("tags", [])
        teacher = validated_data.pop("teacher", None) or self.context["request"].user
        course = Course.objects.create(teacher=teacher, **validated_data)
        if tags:
            course.tags.set(tags)
        for module_data in modules_data:
            Module.objects.create(course=course, **module_data)
        return course

    def update(self, instance, validated_data):
        modules_data = validated_data.pop("modules", None)
        tags = validated_data.pop("tags", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        if modules_data is not None:
            # Free OneToOne quiz links before recreate so reassignment succeeds.
            instance.modules.update(quiz=None)
            instance.modules.all().delete()
            for module_data in modules_data:
                Module.objects.create(course=instance, **module_data)
        return instance


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    student_email = serializers.EmailField(source="student.email", read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "student",
            "student_email",
            "course",
            "credits_spent",
            "progress_percent",
            "enrolled_at",
        )
        read_only_fields = fields


class ModuleProgressSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source="module.title", read_only=True)

    class Meta:
        model = ModuleProgress
        fields = (
            "id",
            "module",
            "module_title",
            "completed",
            "completed_at",
        )


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = (
            "id",
            "quiz",
            "score",
            "passed",
            "answers",
            "created_at",
        )
        read_only_fields = fields


class QuizSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Map of question_id -> choice_id, e.g. {"1": 3}',
    )


class BulkEmailSerializer(serializers.Serializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()
    include_progress = serializers.BooleanField(default=True)


class StudentProgressSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)
    student_name = serializers.SerializerMethodField()
    quiz_attempts = QuizAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "student",
            "student_email",
            "student_name",
            "progress_percent",
            "enrolled_at",
            "quiz_attempts",
        )

    def get_student_name(self, obj):
        full = f"{obj.student.first_name} {obj.student.last_name}".strip()
        return full or obj.student.email
