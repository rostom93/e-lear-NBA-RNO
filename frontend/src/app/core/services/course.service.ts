import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, map, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  BulkEmailPayload,
  Course,
  CourseFilters,
  CourseWritePayload,
  Enrollment,
  Quiz,
  QuizAttempt,
  QuizWritePayload,
  StudentProgress,
  Tag,
} from '../models/course.model';

type ListResponse<T> = T[] | { results: T[] };

function asList<T>(payload: ListResponse<T>): T[] {
  return Array.isArray(payload) ? payload : (payload.results ?? []);
}

@Injectable({ providedIn: 'root' })
export class CourseService {
  private readonly http = inject(HttpClient);

  readonly courses = signal<Course[]>([]);
  readonly tags = signal<Tag[]>([]);
  readonly enrollments = signal<Enrollment[]>([]);
  readonly loading = signal(false);

  listCourses(filters: CourseFilters = {}): Observable<Course[]> {
    this.loading.set(true);
    let params = new HttpParams();
    if (filters.tags) params = params.set('tags', filters.tags);
    if (filters.category) params = params.set('category', filters.category);
    if (filters.level) params = params.set('level', filters.level);
    if (filters.content_focus) params = params.set('content_focus', filters.content_focus);
    if (filters.mine) params = params.set('mine', '1');

    return this.http
      .get<ListResponse<Course>>(`${environment.apiUrl}/courses/`, { params })
      .pipe(
        map((payload) => asList(payload)),
        tap({
          next: (courses) => {
            this.courses.set(courses);
            this.loading.set(false);
          },
          error: () => this.loading.set(false),
        }),
      );
  }

  getCourse(id: number): Observable<Course> {
    return this.http.get<Course>(`${environment.apiUrl}/courses/${id}/`);
  }

  createCourse(payload: CourseWritePayload): Observable<CourseWritePayload & { id: number }> {
    return this.http.post<CourseWritePayload & { id: number }>(
      `${environment.apiUrl}/courses/`,
      payload,
    );
  }

  updateCourse(
    id: number,
    payload: CourseWritePayload,
  ): Observable<CourseWritePayload & { id: number }> {
    return this.http.patch<CourseWritePayload & { id: number }>(
      `${environment.apiUrl}/courses/${id}/`,
      payload,
    );
  }

  deleteCourse(id: number): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/courses/${id}/`);
  }

  createQuiz(payload: QuizWritePayload): Observable<Quiz> {
    return this.http.post<Quiz>(`${environment.apiUrl}/quizzes/`, payload);
  }

  listCourseStudents(courseId: number): Observable<StudentProgress[]> {
    return this.http.get<StudentProgress[]>(
      `${environment.apiUrl}/courses/${courseId}/students/`,
    );
  }

  sendBulkEmail(
    courseId: number,
    payload: BulkEmailPayload,
  ): Observable<{ sent: number }> {
    return this.http.post<{ sent: number }>(
      `${environment.apiUrl}/courses/${courseId}/bulk-email/`,
      payload,
    );
  }

  listTags(): Observable<Tag[]> {
    return this.http.get<ListResponse<Tag>>(`${environment.apiUrl}/tags/`).pipe(
      map((payload) => asList(payload)),
      tap((tags) => this.tags.set(tags)),
    );
  }

  enroll(courseId: number): Observable<Enrollment> {
    return this.http
      .post<Enrollment>(`${environment.apiUrl}/courses/${courseId}/enroll/`, {})
      .pipe(tap((enrollment) => this.enrollments.update((list) => [enrollment, ...list])));
  }

  listEnrollments(): Observable<Enrollment[]> {
    return this.http.get<ListResponse<Enrollment>>(`${environment.apiUrl}/enrollments/`).pipe(
      map((payload) => asList(payload)),
      tap((enrollments) => this.enrollments.set(enrollments)),
    );
  }

  getEnrollment(id: number): Observable<Enrollment> {
    return this.http.get<Enrollment>(`${environment.apiUrl}/enrollments/${id}/`);
  }

  completeModule(enrollmentId: number, moduleId: number): Observable<{
    progress: { id: number; module: number; completed: boolean };
    enrollment: Enrollment;
  }> {
    return this.http
      .post<{
        progress: { id: number; module: number; completed: boolean };
        enrollment: Enrollment;
      }>(`${environment.apiUrl}/enrollments/${enrollmentId}/modules/${moduleId}/complete/`, {})
      .pipe(
        tap(({ enrollment }) => {
          this.enrollments.update((list) =>
            list.map((item) => (item.id === enrollment.id ? enrollment : item)),
          );
        }),
      );
  }

  submitQuiz(
    enrollmentId: number,
    quizId: number,
    answers: Record<string, number>,
  ): Observable<{ attempt: QuizAttempt; enrollment: Enrollment }> {
    return this.http
      .post<{ attempt: QuizAttempt; enrollment: Enrollment }>(
        `${environment.apiUrl}/enrollments/${enrollmentId}/quizzes/${quizId}/submit/`,
        { answers },
      )
      .pipe(
        tap(({ enrollment }) => {
          this.enrollments.update((list) =>
            list.map((item) => (item.id === enrollment.id ? enrollment : item)),
          );
        }),
      );
  }

  toggleCourseActive(courseId: number): Observable<Course> {
    return this.http
      .post<Course>(`${environment.apiUrl}/courses/${courseId}/toggle_active/`, {})
      .pipe(
        tap((updated) => {
          this.courses.update((list) =>
            list.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)),
          );
        }),
      );
  }
}
