import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../core/services/auth.service';
import { StudentDashboardComponent } from './dashboard.component';

describe('StudentDashboardComponent', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StudentDashboardComponent],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    const auth = TestBed.inject(AuthService);
    auth.currentUser.set({
      id: 3,
      email: 'guest@gmail.com',
      username: 'guest',
      first_name: 'Gary',
      last_name: 'Guest',
      role: 'STUDENT',
      credit_balance: 500,
      is_active: true,
      date_joined: '2026-01-01T00:00:00Z',
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lists student enrollments', () => {
    const fixture = TestBed.createComponent(StudentDashboardComponent);
    fixture.detectChanges();

    const req = http.expectOne(`${environment.apiUrl}/enrollments/`);
    req.flush([
      {
        id: 11,
        student: 3,
        student_email: 'guest@gmail.com',
        course: {
          id: 1,
          title: 'Python for Beginners',
          slug: 'python-for-beginners',
          description: 'Intro',
          teacher: 2,
          teacher_email: 'teacher@platform.com',
          price_credits: 100,
          level: 'BEGINNER',
          category: 'Programming',
          content_focus: 'MIXED',
          tags: [],
          is_active: true,
          modules_count: 3,
          created_at: '2026-01-01T00:00:00Z',
        },
        credits_spent: 100,
        progress_percent: 33,
        enrolled_at: '2026-01-02T00:00:00Z',
      },
    ]);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Python for Beginners');
    expect(fixture.nativeElement.textContent).toContain('33%');
  });
});
