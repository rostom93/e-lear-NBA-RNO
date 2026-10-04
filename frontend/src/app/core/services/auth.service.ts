import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, map, of, switchMap, tap, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  LoginRequest,
  RefreshResponse,
  RegisterRequest,
  RegisterResponse,
  TokenResponse,
} from '../models/auth.model';
import { User, UserRole } from '../models/user.model';

const ACCESS_KEY = 'edulearn-access';
const REFRESH_KEY = 'edulearn-refresh';
const USER_KEY = 'edulearn-user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  readonly accessToken = signal<string | null>(localStorage.getItem(ACCESS_KEY));
  readonly refreshToken = signal<string | null>(localStorage.getItem(REFRESH_KEY));
  readonly currentUser = signal<User | null>(this.readStoredUser());

  readonly isAuthenticated = computed(() => !!this.accessToken());
  readonly role = computed(() => this.currentUser()?.role ?? null);
  readonly creditBalance = computed(() => this.currentUser()?.credit_balance ?? 0);

  login(payload: LoginRequest): Observable<User> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/token/`, payload)
      .pipe(
        tap((response) => this.persistSession(response)),
        map((response) => response.user),
        catchError((error) => throwError(() => error)),
      );
  }

  register(payload: RegisterRequest): Observable<RegisterResponse> {
    return this.http.post<RegisterResponse>(`${environment.apiUrl}/auth/register/`, payload);
  }

  /** Creates the account then signs the new student in directly. */
  registerAndLogin(payload: RegisterRequest): Observable<User> {
    return this.register(payload).pipe(
      switchMap(() => this.login({ email: payload.email, password: payload.password })),
    );
  }

  clearSession(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    this.accessToken.set(null);
    this.refreshToken.set(null);
    this.currentUser.set(null);
  }

  logout(): void {
    this.clearSession();
    void this.router.navigate(['/auth/login']);
  }

  refreshAccessToken(): Observable<string> {
    const refresh = this.refreshToken();
    if (!refresh) {
      return throwError(() => new Error('Missing refresh token'));
    }
    return this.http
      .post<RefreshResponse>(`${environment.apiUrl}/auth/token/refresh/`, { refresh })
      .pipe(
        tap((response) => {
          localStorage.setItem(ACCESS_KEY, response.access);
          this.accessToken.set(response.access);
        }),
        map((response) => response.access),
      );
  }

  loadProfile(): Observable<User | null> {
    if (!this.accessToken()) {
      return of(null);
    }
    return this.http.get<User>(`${environment.apiUrl}/auth/me/`).pipe(
      tap((user) => {
        this.currentUser.set(user);
        localStorage.setItem(USER_KEY, JSON.stringify(user));
      }),
      catchError(() => {
        this.logout();
        return of(null);
      }),
    );
  }

  updateCreditBalance(balance: number): void {
    const user = this.currentUser();
    if (!user) {
      return;
    }
    const updated = { ...user, credit_balance: balance };
    this.currentUser.set(updated);
    localStorage.setItem(USER_KEY, JSON.stringify(updated));
  }

  hasRole(...roles: UserRole[]): boolean {
    const role = this.role();
    return !!role && roles.includes(role);
  }

  dashboardRouteForRole(role: UserRole | null = this.role()): string {
    switch (role) {
      case 'ADMIN':
        return '/admin';
      case 'TEACHER':
        return '/teacher';
      case 'STUDENT':
        return '/student';
      default:
        return '/auth/login';
    }
  }

  private persistSession(response: TokenResponse): void {
    localStorage.setItem(ACCESS_KEY, response.access);
    localStorage.setItem(REFRESH_KEY, response.refresh);
    localStorage.setItem(USER_KEY, JSON.stringify(response.user));
    this.accessToken.set(response.access);
    this.refreshToken.set(response.refresh);
    this.currentUser.set(response.user);
  }

  private readStoredUser(): User | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  }
}
