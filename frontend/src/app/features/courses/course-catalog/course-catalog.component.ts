import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { Course, Tag } from '../../../core/models/course.model';
import { CourseService } from '../../../core/services/course.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-course-catalog',
  imports: [ReactiveFormsModule, RouterLink, TranslatePipe],
  templateUrl: './course-catalog.component.html',
  styleUrl: './course-catalog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CourseCatalogComponent implements OnInit {
  private readonly coursesApi = inject(CourseService);
  private readonly fb = inject(FormBuilder);

  readonly courses = signal<Course[]>([]);
  readonly tags = signal<Tag[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);

  readonly filters = this.fb.nonNullable.group({
    tags: [''],
    category: [''],
    level: [''],
    content_focus: [''],
  });

  ngOnInit(): void {
    this.coursesApi.listTags().subscribe({
      next: (tags) => this.tags.set(tags),
    });
    this.reload();
  }

  reload(): void {
    this.error.set(false);
    this.loading.set(true);
    const value = this.filters.getRawValue();
    this.coursesApi
      .listCourses({
        tags: value.tags || undefined,
        category: value.category || undefined,
        level: value.level || undefined,
        content_focus: value.content_focus || undefined,
      })
      .subscribe({
        next: (courses) => {
          this.courses.set(courses);
          this.loading.set(false);
        },
        error: () => {
          this.courses.set([]);
          this.loading.set(false);
          this.error.set(true);
        },
      });
  }

  reset(): void {
    this.filters.reset({
      tags: '',
      category: '',
      level: '',
      content_focus: '',
    });
    this.reload();
  }
}
