from django.contrib import admin

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


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = (
        "order",
        "title",
        "module_type",
        "pdf_url",
        "video_url",
        "quiz",
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "teacher",
        "price_credits",
        "level",
        "category",
        "is_active",
        "created_at",
    )
    list_filter = ("level", "content_focus", "is_active", "category")
    search_fields = ("title", "description", "teacher__email")
    filter_horizontal = ("tags",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ModuleInline]


class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 2


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "passing_score", "created_at")
    search_fields = ("title",)
    inlines = [QuizQuestionInline]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order", "text")
    list_filter = ("quiz",)
    inlines = [QuizChoiceInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "module_type")
    list_filter = ("module_type", "course")
    search_fields = ("title", "course__title")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "credits_spent",
        "progress_percent",
        "enrolled_at",
    )
    list_filter = ("course",)
    search_fields = ("student__email", "course__title")


@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "module", "completed", "completed_at")
    list_filter = ("completed",)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "quiz", "score", "passed", "created_at")
    list_filter = ("passed", "quiz")
