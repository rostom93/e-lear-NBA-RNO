import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { forkJoin, of, switchMap } from 'rxjs';

import {
  ContentFocus,
  CourseLevel,
  CourseWritePayload,
  ModuleType,
  ModuleWritePayload,
  Tag,
  VideoProvider,
} from '../../../core/models/course.model';
import { CourseService } from '../../../core/services/course.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-course-form',
  imports: [ReactiveFormsModule, RouterLink, TranslatePipe],
  templateUrl: './course-form.component.html',
  styleUrl: './course-form.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CourseFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly coursesApi = inject(CourseService);

  readonly tags = signal<Tag[]>([]);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly error = signal(false);
  readonly errorDetail = signal('');
  readonly success = signal(false);
  readonly courseId = signal<number | null>(null);

  readonly form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    description: ['', Validators.required],
    price_credits: [100, [Validators.required, Validators.min(0)]],
    level: this.fb.nonNullable.control<CourseLevel>('BEGINNER', Validators.required),
    category: ['', Validators.required],
    content_focus: this.fb.nonNullable.control<ContentFocus>('MIXED', Validators.required),
    tag_ids: this.fb.nonNullable.control<number[]>([]),
    is_active: [true],
    modules: this.fb.nonNullable.array([this.createModuleGroup(1, 'PDF')]),
  });

  get modules(): FormArray {
    return this.form.controls.modules;
  }

  ngOnInit(): void {
    this.coursesApi.listTags().subscribe({
      next: (tags) => this.tags.set(tags),
    });

    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      return;
    }
    this.courseId.set(id);
    this.loading.set(true);
    this.coursesApi.getCourse(id).subscribe({
      next: (course) => {
        this.modules.clear();
        for (const module of course.modules ?? []) {
          this.modules.push(
            this.createModuleGroup(module.order, module.module_type, {
              title: module.title,
              pdf_url: module.pdf_url,
              video_url: module.video_url,
              video_provider: module.video_provider || 'YOUTUBE',
              captions_url: module.captions_url,
              transcript: module.transcript,
              quiz_title: module.quiz?.title ?? '',
              quiz_question: module.quiz?.questions?.[0]?.text ?? '',
              quiz_correct: module.quiz?.questions?.[0]?.choices?.find((c) => c)?.text ?? '',
              quiz_wrong:
                module.quiz?.questions?.[0]?.choices?.find((c, idx) => idx > 0)?.text ?? '',
              existing_quiz_id: module.quiz?.id ?? null,
            }),
          );
        }
        if (this.modules.length === 0) {
          this.modules.push(this.createModuleGroup(1, 'PDF'));
        }
        this.form.patchValue({
          title: course.title,
          description: course.description,
          price_credits: course.price_credits,
          level: course.level,
          category: course.category,
          content_focus: course.content_focus,
          tag_ids: course.tags.map((tag) => tag.id),
          is_active: course.is_active,
        });
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }

  addModule(): void {
    this.modules.push(this.createModuleGroup(this.modules.length + 1, 'PDF'));
  }

  removeModule(index: number): void {
    if (this.modules.length === 1) {
      return;
    }
    this.modules.removeAt(index);
    this.modules.controls.forEach((control, i) => {
      control.patchValue({ order: i + 1 });
    });
  }

  toggleTag(tagId: number, checked: boolean): void {
    const current = new Set(this.form.controls.tag_ids.value);
    if (checked) {
      current.add(tagId);
    } else {
      current.delete(tagId);
    }
    this.form.controls.tag_ids.setValue([...current]);
  }

  isTagSelected(tagId: number): boolean {
    return this.form.controls.tag_ids.value.includes(tagId);
  }

  showError(control: AbstractControl | null): boolean {
    return !!control && control.invalid && (control.dirty || control.touched);
  }

  submit(): void {
    this.error.set(false);
    this.errorDetail.set('');
    this.success.set(false);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.error.set(true);
      this.errorDetail.set('teacher.error.validation');
      return;
    }

    this.saving.set(true);
    const raw = this.form.getRawValue();

    const quizCreates = raw.modules.map((module) => {
      if (module.module_type !== 'QUIZ') {
        return of<number | null>(null);
      }
      if (module.existing_quiz_id) {
        return of(module.existing_quiz_id);
      }
      return this.coursesApi
        .createQuiz({
          title: module.quiz_title.trim() || `${raw.title} Quiz`,
          passing_score: 60,
          questions: [
            {
              text: module.quiz_question.trim() || 'Sample question?',
              order: 1,
              choices: [
                { text: module.quiz_correct.trim() || 'Yes', is_correct: true },
                { text: module.quiz_wrong.trim() || 'No', is_correct: false },
              ],
            },
          ],
        })
        .pipe(switchMap((quiz) => of(quiz.id)));
    });

    forkJoin(quizCreates)
      .pipe(
        switchMap((quizIds) => {
          const modules: ModuleWritePayload[] = raw.modules.map((module, index) => {
            const type = module.module_type as ModuleType;
            const provider =
              type === 'VIDEO'
                ? ((module.video_provider || 'YOUTUBE') as VideoProvider)
                : ('' as VideoProvider);
            return {
              title: module.title.trim(),
              order: index + 1,
              module_type: type,
              pdf_url: type === 'PDF' ? this.normalizeUrl(module.pdf_url) : '',
              video_url: type === 'VIDEO' ? this.normalizeUrl(module.video_url) : '',
              video_provider: provider,
              captions_url: type === 'VIDEO' ? this.normalizeUrl(module.captions_url) : '',
              transcript: type === 'VIDEO' ? module.transcript.trim() : '',
              quiz: type === 'QUIZ' ? quizIds[index] : null,
            };
          });

          const payload: CourseWritePayload = {
            title: raw.title.trim(),
            description: raw.description.trim(),
            price_credits: Number(raw.price_credits),
            level: raw.level,
            category: raw.category.trim(),
            content_focus: raw.content_focus,
            tag_ids: raw.tag_ids,
            is_active: raw.is_active,
            modules,
          };

          const id = this.courseId();
          return id
            ? this.coursesApi.updateCourse(id, payload)
            : this.coursesApi.createCourse(payload);
        }),
      )
      .subscribe({
        next: (course) => {
          this.saving.set(false);
          this.success.set(true);
          // After an edit, land on the preview so the result is immediately visible;
          // after a create, land on the dashboard where the new course is listed.
          if (this.courseId()) {
            void this.router.navigate(['/teacher/courses', course.id, 'preview']);
          } else {
            void this.router.navigate(['/teacher']);
          }
        },
        error: (err: unknown) => {
          this.saving.set(false);
          this.error.set(true);
          this.errorDetail.set(this.extractApiError(err));
        },
      });
  }

  private normalizeUrl(value: string | null | undefined): string {
    const trimmed = (value ?? '').trim();
    if (!trimmed) {
      return '';
    }
    if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(trimmed)) {
      return trimmed;
    }
    return `https://${trimmed}`;
  }

  private extractApiError(err: unknown): string {
    if (!(err instanceof HttpErrorResponse)) {
      return '';
    }
    const data = err.error;
    if (typeof data === 'string' && data.trim()) {
      return data.slice(0, 240);
    }
    if (data && typeof data === 'object') {
      const detail = (data as { detail?: unknown }).detail;
      if (typeof detail === 'string') {
        return detail;
      }
      const chunks: string[] = [];
      const walk = (node: unknown, prefix = ''): void => {
        if (typeof node === 'string') {
          chunks.push(prefix ? `${prefix}: ${node}` : node);
          return;
        }
        if (Array.isArray(node)) {
          node.forEach((item) => walk(item, prefix));
          return;
        }
        if (node && typeof node === 'object') {
          for (const [key, value] of Object.entries(node)) {
            walk(value, prefix ? `${prefix}.${key}` : key);
          }
        }
      };
      walk(data);
      return chunks.slice(0, 3).join(' · ');
    }
    return '';
  }

  private createModuleGroup(
    order: number,
    moduleType: ModuleType,
    values?: Partial<{
      title: string;
      pdf_url: string;
      video_url: string;
      video_provider: string;
      captions_url: string;
      transcript: string;
      quiz_title: string;
      quiz_question: string;
      quiz_correct: string;
      quiz_wrong: string;
      existing_quiz_id: number | null;
    }>,
  ) {
    return this.fb.nonNullable.group({
      title: [values?.title ?? `Module ${order}`, Validators.required],
      order: [order],
      module_type: [moduleType, Validators.required],
      pdf_url: [values?.pdf_url ?? ''],
      video_url: [values?.video_url ?? ''],
      video_provider: [values?.video_provider ?? 'YOUTUBE'],
      captions_url: [values?.captions_url ?? ''],
      transcript: [values?.transcript ?? ''],
      quiz_title: [values?.quiz_title ?? ''],
      quiz_question: [values?.quiz_question ?? ''],
      quiz_correct: [values?.quiz_correct ?? ''],
      quiz_wrong: [values?.quiz_wrong ?? ''],
      existing_quiz_id: this.fb.control<number | null>(values?.existing_quiz_id ?? null),
    });
  }
}
