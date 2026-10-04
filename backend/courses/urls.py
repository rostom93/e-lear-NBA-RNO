from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminStatsView, CourseViewSet, EnrollmentViewSet, QuizViewSet, TagViewSet

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tags")
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollments")
router.register(r"quizzes", QuizViewSet, basename="quizzes")

urlpatterns = [
    path("admin/stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("", include(router.urls)),
]
