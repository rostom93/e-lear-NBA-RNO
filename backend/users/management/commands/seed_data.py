"""
Idempotent seed for the E-Learning platform.

Usage:
    python manage.py seed_data
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Course, Module, Quiz, QuizChoice, QuizQuestion, Tag
from payments.models import CreditPack, Transaction
from users.models import CustomUser


def upsert_user(*, email, password, role, credit_balance=0, **extra):
    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "role": role,
            "credit_balance": credit_balance,
            **extra,
        },
    )
    user.username = email
    user.role = role
    user.credit_balance = credit_balance
    for key, value in extra.items():
        setattr(user, key, value)
    user.set_password(password)
    user.save()
    return user, created


def ensure_quiz(title, questions):
    """
    questions: list of (text, [(choice_text, is_correct), ...])
    """
    quiz, _ = Quiz.objects.get_or_create(
        title=title,
        defaults={"passing_score": 60},
    )
    quiz.passing_score = 60
    quiz.save(update_fields=["passing_score"])

    if quiz.questions.exists():
        return quiz

    for order, (text, choices) in enumerate(questions, start=1):
        question = QuizQuestion.objects.create(quiz=quiz, text=text, order=order)
        for choice_text, is_correct in choices:
            QuizChoice.objects.create(
                question=question,
                text=choice_text,
                is_correct=is_correct,
            )
    return quiz


def ensure_course_with_modules(
    *,
    title,
    slug,
    description,
    teacher,
    price_credits,
    level,
    category,
    content_focus,
    tags,
    pdf_url,
    video_url,
    video_provider,
    transcript,
    quiz_title,
    quiz_questions,
):
    course, created = Course.objects.get_or_create(
        slug=slug,
        defaults={
            "title": title,
            "description": description,
            "teacher": teacher,
            "price_credits": price_credits,
            "level": level,
            "category": category,
            "content_focus": content_focus,
            "is_active": True,
        },
    )
    course.title = title
    course.description = description
    course.teacher = teacher
    course.price_credits = price_credits
    course.level = level
    course.category = category
    course.content_focus = content_focus
    course.is_active = True
    course.save()
    course.tags.set(tags)

    if course.modules.exists():
        return course, created

    quiz = ensure_quiz(quiz_title, quiz_questions)

    Module.objects.create(
        course=course,
        title=f"{title} — Support PDF",
        order=1,
        module_type=Module.ModuleType.PDF,
        pdf_url=pdf_url,
    )
    Module.objects.create(
        course=course,
        title=f"{title} — Vidéo",
        order=2,
        module_type=Module.ModuleType.VIDEO,
        video_url=video_url,
        video_provider=video_provider,
        captions_url="https://example.com/captions/en.vtt",
        transcript=transcript,
    )
    Module.objects.create(
        course=course,
        title=f"{title} — Quiz",
        order=3,
        module_type=Module.ModuleType.QUIZ,
        quiz=quiz,
    )
    return course, created


class Command(BaseCommand):
    help = "Seed demo users, courses, packs and transactions (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding platform data...")

        admin, admin_created = upsert_user(
            email="admin@platform.com",
            password="Admin123!",
            role=CustomUser.Role.ADMIN,
            credit_balance=0,
            is_staff=True,
            is_superuser=True,
            first_name="Admin",
            last_name="Platform",
        )
        teacher, teacher_created = upsert_user(
            email="teacher@platform.com",
            password="Teacher123!",
            role=CustomUser.Role.TEACHER,
            credit_balance=0,
            is_staff=False,
            is_superuser=False,
            first_name="Tina",
            last_name="Teacher",
        )
        guest, guest_created = upsert_user(
            email="guest@gmail.com",
            password="Guest123!",
            role=CustomUser.Role.STUDENT,
            credit_balance=500,
            is_staff=False,
            is_superuser=False,
            first_name="Gary",
            last_name="Guest",
        )

        packs = []
        for name, credits, price in (
            ("Starter", 100, "9.99"),
            ("Pro", 300, "24.99"),
            ("Ultimate", 500, "39.99"),
        ):
            pack, _ = CreditPack.objects.get_or_create(
                name=name,
                defaults={
                    "credits": credits,
                    "price_euros": Decimal(price),
                    "is_active": True,
                },
            )
            pack.credits = credits
            pack.price_euros = Decimal(price)
            pack.is_active = True
            pack.save()
            packs.append(pack)

        tags = {}
        for tag_name in ("#Angular", "#Python", "#AI"):
            tag, _ = Tag.objects.get_or_create(
                name=tag_name,
                defaults={"slug": tag_name.lstrip("#").lower()},
            )
            tags[tag_name] = tag

        courses_spec = [
            {
                "title": "Angular Fundamentals",
                "slug": "angular-fundamentals",
                "description": (
                    "Apprenez les bases d'Angular : composants standalone, "
                    "signals, routing et formulaires réactifs."
                ),
                "price_credits": 120,
                "level": Course.Level.BEGINNER,
                "category": "Frontend",
                "content_focus": Course.ContentFocus.MIXED,
                "tags": [tags["#Angular"]],
                "pdf_url": "https://example.com/courses/angular/handbook.pdf",
                "video_url": "https://www.youtube.com/watch?v=3qBXWUpoPHo",
                "video_provider": Module.VideoProvider.YOUTUBE,
                "transcript": (
                    "Bienvenue dans Angular Fundamentals. "
                    "Nous verrons les composants standalone et les signals."
                ),
                "quiz_title": "Quiz Angular Fundamentals",
                "quiz_questions": [
                    (
                        "Quel décorateur définit un composant Angular ?",
                        [("@Component", True), ("@Injectable", False), ("@NgModule", False)],
                    ),
                    (
                        "Les Signals sont-ils recommandés pour l'état local ?",
                        [("Oui", True), ("Non", False)],
                    ),
                ],
            },
            {
                "title": "Python for Beginners",
                "slug": "python-for-beginners",
                "description": (
                    "Introduction à Python : syntaxe, structures de données, "
                    "fonctions et premiers scripts."
                ),
                "price_credits": 100,
                "level": Course.Level.BEGINNER,
                "category": "Programming",
                "content_focus": Course.ContentFocus.MIXED,
                "tags": [tags["#Python"]],
                "pdf_url": "https://example.com/courses/python/handbook.pdf",
                "video_url": "https://www.youtube.com/watch?v=kqtD5dpn9C8",
                "video_provider": Module.VideoProvider.YOUTUBE,
                "transcript": (
                    "Python est un langage lisible et polyvalent. "
                    "Commençons par les variables et les listes."
                ),
                "quiz_title": "Quiz Python Beginners",
                "quiz_questions": [
                    (
                        "Quel mot-clé définit une fonction en Python ?",
                        [("def", True), ("function", False), ("func", False)],
                    ),
                    (
                        "Quelle structure est mutable ?",
                        [("list", True), ("tuple", False), ("str", False)],
                    ),
                ],
            },
            {
                "title": "Introduction to AI",
                "slug": "introduction-to-ai",
                "description": (
                    "Découvrez l'intelligence artificielle : concepts, "
                    "machine learning et cas d'usage concrets."
                ),
                "price_credits": 150,
                "level": Course.Level.INTERMEDIATE,
                "category": "Data Science",
                "content_focus": Course.ContentFocus.MIXED,
                "tags": [tags["#AI"]],
                "pdf_url": "https://example.com/courses/ai/handbook.pdf",
                "video_url": "https://vimeo.com/148751763",
                "video_provider": Module.VideoProvider.VIMEO,
                "transcript": (
                    "L'IA regroupe des techniques permettant aux machines "
                    "d'apprendre à partir de données."
                ),
                "quiz_title": "Quiz Introduction to AI",
                "quiz_questions": [
                    (
                        "Le supervised learning utilise-t-il des labels ?",
                        [("Oui", True), ("Non", False)],
                    ),
                    (
                        "Quel est un exemple de modèle de langage ?",
                        [("LLM", True), ("CSS", False), ("SQL only", False)],
                    ),
                ],
            },
        ]

        course_results = []
        for spec in courses_spec:
            course, created = ensure_course_with_modules(teacher=teacher, **spec)
            course_results.append((course, created))

        # Historical SUCCESS transactions (do not alter the fixed demo balance).
        seed_tx_specs = [
            (guest, packs[0], Transaction.Status.SUCCESS),
            (guest, packs[1], Transaction.Status.SUCCESS),
            (guest, packs[0], Transaction.Status.FAILED),
        ]
        created_tx = 0
        for user, pack, tx_status in seed_tx_specs:
            exists = Transaction.objects.filter(
                user=user,
                pack=pack,
                status=tx_status,
                credits=pack.credits,
            ).exists()
            if not exists:
                Transaction.objects.create(
                    user=user,
                    pack=pack,
                    credits=pack.credits,
                    amount_euros=pack.price_euros,
                    status=tx_status,
                )
                created_tx += 1

        # Keep demo balances stable after re-seed.
        guest.credit_balance = 500
        guest.save(update_fields=["credit_balance"])

        self.stdout.write(self.style.SUCCESS("Seed completed."))
        self.stdout.write(
            f"  Users: admin={'created' if admin_created else 'updated'}, "
            f"teacher={'created' if teacher_created else 'updated'}, "
            f"guest={'created' if guest_created else 'updated'}"
        )
        self.stdout.write(f"  Credit packs: {len(packs)}")
        self.stdout.write(f"  Tags: {Tag.objects.count()}")
        self.stdout.write(
            "  Courses: "
            + ", ".join(
                f"{c.slug}({'new' if created else 'exists'})"
                for c, created in course_results
            )
        )
        self.stdout.write(f"  New transactions: {created_tx}")
        self.stdout.write(
            "  Accounts:\n"
            "    admin@platform.com / Admin123!\n"
            "    teacher@platform.com / Teacher123!\n"
            "    guest@gmail.com / Guest123! (500 credits)"
        )
