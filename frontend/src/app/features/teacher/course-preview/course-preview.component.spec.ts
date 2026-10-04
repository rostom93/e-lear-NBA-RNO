import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';

import { environment } from '../../../../environments/environment';
import { CoursePreviewComponent } from './course-preview.component';

describe('CoursePreviewComponent', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CoursePreviewComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id: '12' }) } },
        },
      ],
    }).compileComponents();

    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('renders the course as a student would see it and selects the first module', () => {
    const fixture = TestBed.createComponent(CoursePreviewComponent);
    fixture.detectChanges();

    http.expectOne(`${environment.apiUrl}/courses/12/`).flush({
      id: 12,
      title: 'Signals in Depth',
      slug: 'signals-in-depth',
      description: 'Reactive Angular',
      teacher: 2,
      teacher_email: 'teacher@platform.com',
      price_credits: 80,
      level: 'INTERMEDIATE',
      category: 'Frontend',
      content_focus: 'MIXED',
      tags: [{ id: 3, name: '#Signals', slug: 'signals' }],
      is_active: false,
      modules_count: 2,
      created_at: '2026-01-01T00:00:00Z',
      modules: [
        {
          id: 101,
          title: 'Intro video',
          order: 1,
          module_type: 'VIDEO',
          pdf_url: '',
          video_url: 'https://www.youtube.com/watch?v=abc123',
          video_provider: 'YOUTUBE',
          captions_url: '',
          transcript: '',
          quiz: null,
        },
        {
          id: 102,
          title: 'Final quiz',
          order: 2,
          module_type: 'QUIZ',
          pdf_url: '',
          video_url: '',
          video_provider: '',
          captions_url: '',
          transcript: '',
          quiz: {
            id: 9,
            title: 'Check your knowledge',
            passing_score: 70,
            questions: [
              {
                id: 55,
                text: 'What is a signal?',
                order: 1,
                choices: [
                  { id: 1, text: 'A reactive value' },
                  { id: 2, text: 'A CSS feature' },
                ],
              },
            ],
          },
        },
      ],
    });
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Signals in Depth');
    expect(text).toContain('Intro video');
    expect(fixture.componentInstance.activeModuleId()).toBe(101);
    expect(fixture.componentInstance.embedUrl()).not.toBeNull();

    fixture.componentInstance.selectModule(fixture.componentInstance.modules()[1]);
    fixture.detectChanges();

    expect(fixture.componentInstance.embedUrl()).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('What is a signal?');
    const radios = fixture.nativeElement.querySelectorAll('input[type="radio"]');
    expect(radios.length).toBe(2);
    expect((radios[0] as HTMLInputElement).disabled).toBe(true);
  });
});
