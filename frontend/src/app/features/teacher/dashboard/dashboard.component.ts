import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Course } from '../../../core/models/course.model';
import { CourseService } from '../../../core/services/course.service';
import { TranslationService } from '../../../core/services/translation.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-teacher-dashboard',
  imports: [RouterLink, TranslatePipe],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TeacherDashboardComponent implements OnInit {
  private readonly coursesApi = inject(CourseService);
  private readonly i18n = inject(TranslationService);

  readonly courses = signal<Course[]>([]);
  readonly loading = signal(true);
  readonly error = signal(false);
  readonly deletingId = signal<number | null>(null);

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.error.set(false);
    this.coursesApi.listCourses({ mine: true }).subscribe({
      next: (courses) => {
        this.courses.set(courses);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }

  remove(course: Course): void {
    if (!confirm(this.i18n.t('teacher.confirmDelete'))) {
      return;
    }
    this.deletingId.set(course.id);
    this.coursesApi.deleteCourse(course.id).subscribe({
      next: () => {
        this.courses.update((list) => list.filter((item) => item.id !== course.id));
        this.deletingId.set(null);
      },
      error: () => this.deletingId.set(null),
    });
  }
}
