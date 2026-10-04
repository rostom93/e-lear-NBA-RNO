import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { environment } from '../../../../environments/environment';
import { RegisterComponent } from './register.component';

describe('RegisterComponent', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [RegisterComponent],
      providers: [
        provideRouter([{ path: 'student', children: [] }]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('blocks submission when the two passwords differ', () => {
    const fixture = TestBed.createComponent(RegisterComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    component.form.setValue({
      first_name: 'Nina',
      last_name: 'Diop',
      email: 'nina@example.com',
      password: 'Str0ngPass!',
      confirm: 'Other0Pass!',
    });
    component.submit();

    expect(component.form.hasError('mismatch')).toBe(true);
    http.expectNone(`${environment.apiUrl}/auth/register/`);
  });

  it('registers then signs the new student in', () => {
    const fixture = TestBed.createComponent(RegisterComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    component.form.setValue({
      first_name: 'Nina',
      last_name: 'Diop',
      email: 'nina@example.com',
      password: 'Str0ngPass!',
      confirm: 'Str0ngPass!',
    });
    component.submit();

    const registerReq = http.expectOne(`${environment.apiUrl}/auth/register/`);
    expect(registerReq.request.body).toEqual({
      email: 'nina@example.com',
      password: 'Str0ngPass!',
      first_name: 'Nina',
      last_name: 'Diop',
    });
    registerReq.flush({
      email: 'nina@example.com',
      first_name: 'Nina',
      last_name: 'Diop',
      username: 'nina@example.com',
    });

    const loginReq = http.expectOne(`${environment.apiUrl}/auth/token/`);
    loginReq.flush({
      access: 'access-token',
      refresh: 'refresh-token',
      user: {
        id: 42,
        email: 'nina@example.com',
        first_name: 'Nina',
        last_name: 'Diop',
        role: 'STUDENT',
        credit_balance: 0,
        preferred_language: 'FR',
      },
    });

    expect(component.error()).toBe(false);
    expect(component.submitting()).toBe(false);
    expect(localStorage.getItem('edulearn-access')).toBe('access-token');
  });

  it('surfaces the API error detail when the email is already used', () => {
    const fixture = TestBed.createComponent(RegisterComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    component.form.setValue({
      first_name: '',
      last_name: '',
      email: 'student@platform.com',
      password: 'Str0ngPass!',
      confirm: 'Str0ngPass!',
    });
    component.submit();

    http
      .expectOne(`${environment.apiUrl}/auth/register/`)
      .flush(
        { email: ['Un utilisateur avec cet e-mail existe déjà.'] },
        { status: 400, statusText: 'Bad Request' },
      );

    expect(component.error()).toBe(true);
    expect(component.errorDetail()).toContain('existe déjà');
  });
});
