import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ActivatedRoute, RouterLink } from '@angular/router';

import {
  Course,
  Enrollment,
  Module,
  QuizAttempt,
} from '../../../core/models/course.model';
import { CourseService } from '../../../core/services/course.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { toEmbedUrl } from '../../../shared/utils/video.util';

@Component({
  selector: 'app-course-player',
  imports: [ReactiveFormsModule, RouterLink, TranslatePipe],
  templateUrl: './course-player.component.html',
  styleUrl: './course-player.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CoursePlayerComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly coursesApi = inject(CourseService);
  private readonly fb = inject(FormBuilder);
  private readonly sanitizer = inject(DomSanitizer);

  readonly enrollment = signal<Enrollment | null>(null);
  readonly course = signal<Course | null>(null);
  readonly activeModuleId = signal<number | null>(null);
  readonly loading = signal(true);
  readonly error = signal(false);
  readonly completing = signal(false);
  readonly quizResult = signal<QuizAttempt | null>(null);
  readonly quizForm = this.fb.nonNullable.group({});

  readonly modules = computed(() => this.course()?.modules ?? []);
  readonly activeModule = computed(
    () => this.modules().find((module) => module.id === this.activeModuleId()) ?? null,
  );
  readonly embedUrl = computed<SafeResourceUrl | null>(() => {
    const module = this.activeModule();
    if (!module || module.module_type !== 'VIDEO') {
      return null;
    }
    const url = toEmbedUrl(module.video_url, module.video_provider);
    return url ? this.sanitizer.bypassSecurityTrustResourceUrl(url) : null;
  });
  readonly progress = computed(() => this.enrollment()?.progress_percent ?? 0);

  ngOnInit(): void {
    const enrollmentId = Number(this.route.snapshot.paramMap.get('enrollmentId'));
    if (!enrollmentId) {
      this.loading.set(false);
      this.error.set(true);
      return;
    }

    this.coursesApi.getEnrollment(enrollmentId).subscribe({
      next: (enrollment) => {
        this.enrollment.set(enrollment);
        this.coursesApi.getCourse(enrollment.course.id).subscribe({
          next: (course) => {
            this.course.set(course);
            const first = course.modules?.[0];
            if (first) {
              this.selectModule(first);
            }
            this.loading.set(false);
          },
          error: () => {
            this.loading.set(false);
            this.error.set(true);
          },
        });
      },
      error: () => {
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }

  selectModule(module: Module): void {
    this.activeModuleId.set(module.id);
    this.quizResult.set(null);
    this.rebuildQuizForm(module);
  }

  controlName(questionId: number): string {
    return String(questionId);
  }

  completeCurrent(): void {
    const enrollment = this.enrollment();
    const module = this.activeModule();
    if (!enrollment || !module || module.module_type === 'QUIZ') {
      return;
    }
    this.completing.set(true);
    this.coursesApi.completeModule(enrollment.id, module.id).subscribe({
      next: ({ enrollment: updated }) => {
        this.enrollment.set(updated);
        this.completing.set(false);
      },
      error: () => this.completing.set(false),
    });
  }

  submitQuiz(): void {
    const enrollment = this.enrollment();
    const module = this.activeModule();
    const quiz = module?.quiz;
    if (!enrollment || !quiz) {
      return;
    }

    const raw = this.quizForm.getRawValue() as Record<string, number | string>;
    const answers: Record<string, number> = {};
    for (const [key, value] of Object.entries(raw)) {
      if (value === '' || value === null || value === undefined) {
        continue;
      }
      answers[key] = Number(value);
    }

    this.completing.set(true);
    this.coursesApi.submitQuiz(enrollment.id, quiz.id, answers).subscribe({
      next: ({ attempt, enrollment: updated }) => {
        this.quizResult.set(attempt);
        this.enrollment.set(updated);
        this.completing.set(false);
      },
      error: () => this.completing.set(false),
    });
  }

  private rebuildQuizForm(module: Module): void {
    for (const key of Object.keys(this.quizForm.controls)) {
      this.quizForm.removeControl(key);
    }
    if (module.module_type !== 'QUIZ' || !module.quiz) {
      return;
    }
    for (const question of module.quiz.questions) {
      this.quizForm.addControl(String(question.id), this.fb.nonNullable.control(''));
    }
  }
}
