import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { Course, Module } from '../../../core/models/course.model';
import { CourseService } from '../../../core/services/course.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { toEmbedUrl } from '../../../shared/utils/video.util';

@Component({
  selector: 'app-course-preview',
  imports: [RouterLink, TranslatePipe],
  templateUrl: './course-preview.component.html',
  styleUrl: './course-preview.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CoursePreviewComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly coursesApi = inject(CourseService);
  private readonly sanitizer = inject(DomSanitizer);

  readonly course = signal<Course | null>(null);
  readonly activeModuleId = signal<number | null>(null);
  readonly loading = signal(true);
  readonly error = signal(false);

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

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.loading.set(false);
      this.error.set(true);
      return;
    }

    this.coursesApi.getCourse(id).subscribe({
      next: (course) => {
        this.course.set(course);
        const first = course.modules?.[0];
        if (first) {
          this.activeModuleId.set(first.id);
        }
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }

  selectModule(module: Module): void {
    this.activeModuleId.set(module.id);
  }
}
