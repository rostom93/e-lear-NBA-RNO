import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, map, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AdminStats, AdminUser, AdminUserWrite } from '../models/admin.model';
import { UserRole } from '../models/user.model';

type ListResponse<T> = T[] | { results: T[] };

function asList<T>(payload: ListResponse<T>): T[] {
  return Array.isArray(payload) ? payload : (payload.results ?? []);
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);

  readonly stats = signal<AdminStats | null>(null);
  readonly users = signal<AdminUser[]>([]);
  readonly loading = signal(false);

  getStats(): Observable<AdminStats> {
    return this.http
      .get<AdminStats>(`${environment.apiUrl}/admin/stats/`)
      .pipe(tap((stats) => this.stats.set(stats)));
  }

  listUsers(): Observable<AdminUser[]> {
    this.loading.set(true);
    return this.http.get<ListResponse<AdminUser>>(`${environment.apiUrl}/users/`).pipe(
      map((payload) => asList(payload)),
      tap({
        next: (users) => {
          this.users.set(users);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      }),
    );
  }

  createUser(payload: AdminUserWrite): Observable<AdminUser> {
    return this.http
      .post<AdminUser>(`${environment.apiUrl}/users/`, payload)
      .pipe(tap((user) => this.users.update((list) => [user, ...list])));
  }

  updateUser(id: number, payload: Partial<AdminUserWrite>): Observable<AdminUser> {
    return this.http
      .patch<AdminUser>(`${environment.apiUrl}/users/${id}/`, payload)
      .pipe(
        tap((user) =>
          this.users.update((list) => list.map((item) => (item.id === id ? user : item))),
        ),
      );
  }

  setRole(id: number, role: UserRole): Observable<AdminUser> {
    return this.http
      .post<AdminUser>(`${environment.apiUrl}/users/${id}/set_role/`, { role })
      .pipe(
        tap((user) =>
          this.users.update((list) => list.map((item) => (item.id === id ? user : item))),
        ),
      );
  }

  deleteUser(id: number): Observable<void> {
    return this.http
      .delete<void>(`${environment.apiUrl}/users/${id}/`)
      .pipe(tap(() => this.users.update((list) => list.filter((item) => item.id !== id))));
  }
}
