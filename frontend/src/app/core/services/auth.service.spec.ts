import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';

import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([{ path: 'auth/login', children: [] }]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
    vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('stores tokens and user on login', () => {
    let role = '';
    service.login({ email: 'guest@gmail.com', password: 'Guest123!' }).subscribe((user) => {
      role = user.role;
    });

    const req = http.expectOne(`${environment.apiUrl}/auth/token/`);
    expect(req.request.method).toBe('POST');
    req.flush({
      access: 'access-token',
      refresh: 'refresh-token',
      user: {
        id: 1,
        email: 'guest@gmail.com',
        username: 'guest@gmail.com',
        first_name: 'Gary',
        last_name: 'Guest',
        role: 'STUDENT',
        credit_balance: 500,
        is_active: true,
        date_joined: '2026-01-01T00:00:00Z',
      },
    });

    expect(role).toBe('STUDENT');
    expect(service.isAuthenticated()).toBe(true);
    expect(service.accessToken()).toBe('access-token');
    expect(service.creditBalance()).toBe(500);
    expect(localStorage.getItem('edulearn-access')).toBe('access-token');
  });

  it('clears session on logout', () => {
    localStorage.setItem('edulearn-access', 'x');
    service.accessToken.set('x');
    service.logout();
    expect(service.isAuthenticated()).toBe(false);
    expect(localStorage.getItem('edulearn-access')).toBeNull();
  });
});
