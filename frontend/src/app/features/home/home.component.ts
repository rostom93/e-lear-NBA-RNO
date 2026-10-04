import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Course } from '../../core/models/course.model';
import { AuthService } from '../../core/services/auth.service';
import { CourseService } from '../../core/services/course.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-home',
  imports: [RouterLink, TranslatePipe],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly coursesApi = inject(CourseService);

  readonly featured = signal<Course[]>([]);
  readonly loadError = signal(false);

  ngOnInit(): void {
    this.coursesApi.listCourses().subscribe({
      next: (courses) => this.featured.set(courses.slice(0, 3)),
      error: () => this.loadError.set(true),
    });
  }
}
