import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';

import { environment } from '../../../../environments/environment';
import { CourseDetailComponent } from './course-detail.component';

describe('CourseDetailComponent', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CourseDetailComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: convertToParamMap({ id: '7' }) },
          },
        },
      ],
    }).compileComponents();

    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('loads and renders course details', () => {
    const fixture = TestBed.createComponent(CourseDetailComponent);
    fixture.detectChanges();

    const req = http.expectOne(`${environment.apiUrl}/courses/7/`);
    req.flush({
      id: 7,
      title: 'Angular Fundamentals',
      slug: 'angular-fundamentals',
      description: 'Learn Angular',
      teacher: 2,
      teacher_email: 'teacher@platform.com',
      price_credits: 120,
      level: 'BEGINNER',
      category: 'Frontend',
      content_focus: 'MIXED',
      tags: [{ id: 1, name: '#Angular', slug: 'angular' }],
      is_active: true,
      modules_count: 3,
      created_at: '2026-01-01T00:00:00Z',
      modules: [],
    });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Angular Fundamentals');
    expect(fixture.componentInstance.course()?.price_credits).toBe(120);
  });
});
