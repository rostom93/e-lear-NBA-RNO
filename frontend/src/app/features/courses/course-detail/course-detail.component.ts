import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { Course, Enrollment } from '../../../core/models/course.model';
import { AuthService } from '../../../core/services/auth.service';
import { CourseService } from '../../../core/services/course.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-course-detail',
  imports: [RouterLink, TranslatePipe],
  templateUrl: './course-detail.component.html',
  styleUrl: './course-detail.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CourseDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly coursesApi = inject(CourseService);
  readonly auth = inject(AuthService);

  readonly course = signal<Course | null>(null);
  readonly enrollment = signal<Enrollment | null>(null);
  readonly loading = signal(true);
  readonly enrolling = signal(false);
  readonly error = signal<string | null>(null);

  readonly canEnroll = computed(
    () => this.auth.hasRole('STUDENT') && !this.enrollment() && !!this.course(),
  );

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.loading.set(false);
      this.error.set('missing');
      return;
    }

    this.coursesApi.getCourse(id).subscribe({
      next: (course) => {
        this.course.set(course);
        this.loading.set(false);
        if (this.auth.isAuthenticated() && this.auth.hasRole('STUDENT')) {
          this.coursesApi.listEnrollments().subscribe({
            next: (list) => {
              this.enrollment.set(list.find((item) => item.course.id === course.id) ?? null);
            },
          });
        }
      },
      error: () => {
        this.loading.set(false);
        this.error.set('load');
      },
    });
  }

  enroll(): void {
    const course = this.course();
    if (!course) {
      return;
    }
    if (!this.auth.isAuthenticated()) {
      void this.router.navigate(['/auth/login']);
      return;
    }

    this.enrolling.set(true);
    this.error.set(null);
    this.coursesApi.enroll(course.id).subscribe({
      next: (enrollment) => {
        this.enrollment.set(enrollment);
        this.enrolling.set(false);
        this.auth.loadProfile().subscribe();
      },
      error: (err) => {
        this.enrolling.set(false);
        const detail = err?.error?.detail;
        if (typeof detail === 'string' && detail.toLowerCase().includes('insufficient')) {
          this.error.set('credits');
        } else if (typeof detail === 'string' && detail.toLowerCase().includes('already')) {
          this.error.set('already');
        } else {
          this.error.set('enroll');
        }
      },
    });
  }
}
