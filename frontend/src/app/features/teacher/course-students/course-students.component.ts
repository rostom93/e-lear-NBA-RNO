import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { Course, StudentProgress } from '../../../core/models/course.model';
import { CourseService } from '../../../core/services/course.service';
import { TranslationService } from '../../../core/services/translation.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-course-students',
  imports: [ReactiveFormsModule, RouterLink, TranslatePipe],
  templateUrl: './course-students.component.html',
  styleUrl: './course-students.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CourseStudentsComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly coursesApi = inject(CourseService);
  private readonly fb = inject(FormBuilder);
  private readonly i18n = inject(TranslationService);

  readonly course = signal<Course | null>(null);
  readonly students = signal<StudentProgress[]>([]);
  readonly selectedIds = signal<number[]>([]);
  readonly loading = signal(true);
  readonly error = signal(false);
  readonly sending = signal(false);
  readonly sentCount = signal<number | null>(null);
  readonly emailError = signal<string | null>(null);

  readonly emailForm = this.fb.nonNullable.group({
    subject: ['', Validators.required],
    message: ['', Validators.required],
    include_progress: [true],
  });

  ngOnInit(): void {
    const courseId = Number(this.route.snapshot.paramMap.get('id'));
    if (!courseId) {
      this.loading.set(false);
      this.error.set(true);
      return;
    }

    this.coursesApi.getCourse(courseId).subscribe({
      next: (course) => this.course.set(course),
      error: () => this.error.set(true),
    });

    this.coursesApi.listCourseStudents(courseId).subscribe({
      next: (students) => {
        this.students.set(students);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }

  toggleStudent(studentId: number, checked: boolean): void {
    this.selectedIds.update((ids) => {
      const set = new Set(ids);
      if (checked) {
        set.add(studentId);
      } else {
        set.delete(studentId);
      }
      return [...set];
    });
  }

  isSelected(studentId: number): boolean {
    return this.selectedIds().includes(studentId);
  }

  selectAll(checked: boolean): void {
    this.selectedIds.set(checked ? this.students().map((item) => item.student) : []);
  }

  sendEmail(): void {
    this.emailError.set(null);
    this.sentCount.set(null);
    const course = this.course();
    if (!course) {
      return;
    }
    if (this.selectedIds().length === 0) {
      this.emailError.set('none');
      return;
    }
    if (this.emailForm.invalid) {
      this.emailForm.markAllAsTouched();
      return;
    }

    this.sending.set(true);
    const value = this.emailForm.getRawValue();
    this.coursesApi
      .sendBulkEmail(course.id, {
        student_ids: this.selectedIds(),
        subject: value.subject,
        message: value.message,
        include_progress: value.include_progress,
      })
      .subscribe({
        next: (response) => {
          this.sending.set(false);
          this.sentCount.set(response.sent);
        },
        error: () => {
          this.sending.set(false);
          this.emailError.set('error');
        },
      });
  }

  sentLabel(): string {
    return this.i18n.t('teacher.email.sent', { count: this.sentCount() ?? 0 });
  }
}
