import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Course } from '../../../core/models/course.model';
import { CourseService } from '../../../core/services/course.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-admin-moderation',
  imports: [RouterLink, TranslatePipe],
  templateUrl: './moderation.component.html',
  styleUrl: './moderation.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminModerationComponent implements OnInit {
  private readonly coursesApi = inject(CourseService);

  readonly courses = signal<Course[]>([]);
  readonly loading = signal(true);
  readonly error = signal(false);
  readonly togglingId = signal<number | null>(null);
  readonly toggleError = signal(false);

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.error.set(false);
    this.coursesApi.listCourses().subscribe({
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

  toggle(course: Course): void {
    this.togglingId.set(course.id);
    this.toggleError.set(false);
    this.coursesApi.toggleCourseActive(course.id).subscribe({
      next: (updated) => {
        this.courses.update((list) =>
          list.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)),
        );
        this.togglingId.set(null);
      },
      error: () => {
        this.togglingId.set(null);
        this.toggleError.set(true);
      },
    });
  }
}
