from django.core.mail import send_mail
from django.db.models import Avg, Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import CustomUser
from users.permissions import IsAdminRole, IsTeacher, IsTeacherOrAdmin

from .models import Course, Enrollment, Module, Quiz, Tag
from .serializers import (
    BulkEmailSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CourseWriteSerializer,
    EnrollmentSerializer,
    ModuleProgressSerializer,
    QuizAttemptSerializer,
    QuizSubmitSerializer,
    QuizWriteSerializer,
    StudentProgressSerializer,
    TagSerializer,
)
from .services import enroll_student, mark_module_completed, submit_quiz


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class CourseViewSet(viewsets.ModelViewSet):
    """
    Catalog + teacher course management.
    Students/public see active courses; teachers manage their own; admin manages all.
    """

    lookup_field = "pk"

    def get_queryset(self):
        qs = Course.objects.select_related("teacher").prefetch_related(
            "tags", "modules", "modules__quiz", "modules__quiz__questions__choices"
        )
        user = self.request.user
        is_admin = user.is_authenticated and user.role == CustomUser.Role.ADMIN
        is_teacher = user.is_authenticated and user.role == CustomUser.Role.TEACHER

        if self.action in ("list", "retrieve", "enroll"):
            if is_admin:
                pass
            elif is_teacher and self.request.query_params.get("mine") == "1":
                qs = qs.filter(teacher=user)
            elif self.action == "retrieve" and is_teacher:
                # Teachers can open their own courses even when inactive.
                qs = qs.filter(Q(is_active=True) | Q(teacher=user))
            else:
                qs = qs.filter(is_active=True)
        elif self.action in (
            "update",
            "partial_update",
            "destroy",
            "students",
            "bulk_email",
            "toggle_active",
        ):
            if is_admin:
                pass
            elif is_teacher:
                qs = qs.filter(teacher=user)
            else:
                qs = qs.none()
        elif is_teacher:
            qs = qs.filter(teacher=user)
        elif is_admin:
            pass
        else:
            qs = qs.none()

        tags = self.request.query_params.get("tags")
        if tags:
            tag_list = [t.strip().lstrip("#") for t in tags.split(",") if t.strip()]
            qs = qs.filter(
                Q(tags__slug__in=tag_list)
                | Q(tags__name__in=tag_list)
                | Q(tags__name__in=[f"#{t}" for t in tag_list])
            ).distinct()

        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__iexact=category)

        level = self.request.query_params.get("level")
        if level:
            qs = qs.filter(level=level.upper())

        content_focus = self.request.query_params.get(
            "content_focus"
        ) or self.request.query_params.get("content_type")
        if content_focus:
            qs = qs.filter(content_focus=content_focus.upper())

        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return CourseWriteSerializer
        return CourseListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "create":
            return [IsTeacher()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsTeacherOrAdmin()]
        if self.action in ("enroll",):
            return [IsAuthenticated()]
        if self.action in ("toggle_active",):
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

    def perform_update(self, serializer):
        course = self.get_object()
        user = self.request.user
        if user.role == CustomUser.Role.TEACHER and course.teacher_id != user.id:
            self.permission_denied(self.request, message="You can only edit your own courses.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role == CustomUser.Role.TEACHER and instance.teacher_id != user.id:
            self.permission_denied(self.request, message="You can only delete your own courses.")
        instance.delete()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()
        if request.user.role != CustomUser.Role.STUDENT:
            return Response(
                {"detail": "Only students can enroll in courses."},
                status=status.HTTP_403_FORBIDDEN,
            )
        enrollment = enroll_student(request.user, course)
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdminRole])
    def toggle_active(self, request, pk=None):
        course = self.get_object()
        course.is_active = not course.is_active
        course.save(update_fields=["is_active"])
        return Response(CourseListSerializer(course).data)

    @action(
        detail=True,
        methods=["get"],
        url_path="students",
        permission_classes=[IsTeacherOrAdmin],
    )
    def students(self, request, pk=None):
        course = self.get_object()
        if (
            request.user.role == CustomUser.Role.TEACHER
            and course.teacher_id != request.user.id
        ):
            return Response(
                {"detail": "You can only view students of your own courses."},
                status=status.HTTP_403_FORBIDDEN,
            )
        enrollments = course.enrollments.select_related("student").prefetch_related(
            "quiz_attempts"
        )
        return Response(StudentProgressSerializer(enrollments, many=True).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="bulk-email",
        permission_classes=[IsTeacherOrAdmin],
    )
    def bulk_email(self, request, pk=None):
        course = self.get_object()
        if (
            request.user.role == CustomUser.Role.TEACHER
            and course.teacher_id != request.user.id
        ):
            return Response(
                {"detail": "You can only email students of your own courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BulkEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        enrollments = course.enrollments.filter(
            student_id__in=data["student_ids"]
        ).select_related("student")
        if not enrollments.exists():
            return Response(
                {"detail": "No matching enrolled students found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sent = 0
        for enrollment in enrollments:
            body = data["message"]
            if data["include_progress"]:
                body += (
                    f"\n\n---\nProgress on '{course.title}': "
                    f"{enrollment.progress_percent}% complete."
                )
            send_mail(
                subject=data["subject"],
                message=body,
                from_email=None,
                recipient_list=[enrollment.student.email],
                fail_silently=False,
            )
            sent += 1

        return Response({"sent": sent})


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Enrollment.objects.select_related("course", "student").prefetch_related(
            "course__tags"
        )
        if user.role == CustomUser.Role.ADMIN:
            return qs
        if user.role == CustomUser.Role.TEACHER:
            return qs.filter(course__teacher=user)
        return qs.filter(student=user)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"modules/(?P<module_id>[^/.]+)/complete",
    )
    def complete_module(self, request, pk=None, module_id=None):
        enrollment = self.get_object()
        if (
            request.user.role == CustomUser.Role.STUDENT
            and enrollment.student_id != request.user.id
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            module = Module.objects.get(pk=module_id, course=enrollment.course)
        except Module.DoesNotExist:
            return Response(
                {"detail": "Module not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        progress = mark_module_completed(enrollment, module)
        enrollment.refresh_from_db()
        return Response(
            {
                "progress": ModuleProgressSerializer(progress).data,
                "enrollment": EnrollmentSerializer(enrollment).data,
            }
        )

    @action(
        detail=True,
        methods=["post"],
        url_path=r"quizzes/(?P<quiz_id>[^/.]+)/submit",
    )
    def submit_quiz_action(self, request, pk=None, quiz_id=None):
        enrollment = self.get_object()
        if enrollment.student_id != request.user.id and request.user.role != CustomUser.Role.ADMIN:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return Response(
                {"detail": "Quiz not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        attempt = submit_quiz(enrollment, quiz, serializer.validated_data["answers"])
        enrollment.refresh_from_db()
        return Response(
            {
                "attempt": QuizAttemptSerializer(attempt).data,
                "enrollment": EnrollmentSerializer(enrollment).data,
            },
            status=status.HTTP_201_CREATED,
        )


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.prefetch_related("questions__choices")
    serializer_class = QuizWriteSerializer
    permission_classes = [IsTeacherOrAdmin]


class AdminStatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        from payments.models import Transaction

        users_count = CustomUser.objects.count()
        students = CustomUser.objects.filter(role=CustomUser.Role.STUDENT).count()
        teachers = CustomUser.objects.filter(role=CustomUser.Role.TEACHER).count()

        success_tx = Transaction.objects.filter(status=Transaction.Status.SUCCESS)
        credits_sold = success_tx.aggregate(total=Count("id"))
        credits_sum = sum(success_tx.values_list("credits", flat=True))
        revenue = sum(success_tx.values_list("amount_euros", flat=True))

        popular = (
            Course.objects.annotate(enroll_count=Count("enrollments"))
            .order_by("-enroll_count")[:5]
            .values("id", "title", "enroll_count")
        )

        avg_completion = (
            Enrollment.objects.aggregate(avg=Avg("progress_percent"))["avg"] or 0
        )

        return Response(
            {
                "users": {
                    "total": users_count,
                    "students": students,
                    "teachers": teachers,
                },
                "payments": {
                    "successful_transactions": credits_sold["total"] or 0,
                    "credits_sold": credits_sum,
                    "revenue_euros": str(revenue),
                },
                "popular_courses": list(popular),
                "average_completion_percent": round(float(avg_completion), 2),
            }
        )
