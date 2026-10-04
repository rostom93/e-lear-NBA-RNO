import { Routes } from '@angular/router';

import { authGuard } from './core/guards/auth.guard';
import { guestGuard } from './core/guards/guest.guard';
import { roleGuard } from './core/guards/role.guard';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';

export const routes: Routes = [
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/home/home.component').then((m) => m.HomeComponent),
      },
      {
        path: 'courses',
        loadComponent: () =>
          import('./features/courses/course-catalog/course-catalog.component').then(
            (m) => m.CourseCatalogComponent,
          ),
      },
      {
        path: 'courses/:id',
        loadComponent: () =>
          import('./features/courses/course-detail/course-detail.component').then(
            (m) => m.CourseDetailComponent,
          ),
      },
      {
        path: 'auth/login',
        canActivate: [guestGuard],
        loadComponent: () =>
          import('./features/auth/login/login.component').then((m) => m.LoginComponent),
      },
      {
        path: 'auth/register',
        canActivate: [guestGuard],
        loadComponent: () =>
          import('./features/auth/register/register.component').then((m) => m.RegisterComponent),
      },
      {
        path: 'student',
        canActivate: [authGuard, roleGuard('STUDENT')],
        loadComponent: () =>
          import('./features/student/dashboard/dashboard.component').then(
            (m) => m.StudentDashboardComponent,
          ),
      },
      {
        path: 'student/credits',
        canActivate: [authGuard, roleGuard('STUDENT')],
        loadComponent: () =>
          import('./features/student/credits/credits.component').then((m) => m.CreditsComponent),
      },
      {
        path: 'student/learn/:enrollmentId',
        canActivate: [authGuard, roleGuard('STUDENT')],
        loadComponent: () =>
          import('./features/courses/course-player/course-player.component').then(
            (m) => m.CoursePlayerComponent,
          ),
      },
      {
        path: 'teacher',
        canActivate: [authGuard, roleGuard('TEACHER')],
        loadComponent: () =>
          import('./features/teacher/dashboard/dashboard.component').then(
            (m) => m.TeacherDashboardComponent,
          ),
      },
      {
        path: 'teacher/courses/new',
        canActivate: [authGuard, roleGuard('TEACHER')],
        loadComponent: () =>
          import('./features/teacher/course-form/course-form.component').then(
            (m) => m.CourseFormComponent,
          ),
      },
      {
        path: 'teacher/courses/:id/edit',
        canActivate: [authGuard, roleGuard('TEACHER')],
        loadComponent: () =>
          import('./features/teacher/course-form/course-form.component').then(
            (m) => m.CourseFormComponent,
          ),
      },
      {
        path: 'teacher/courses/:id/preview',
        canActivate: [authGuard, roleGuard('TEACHER')],
        loadComponent: () =>
          import('./features/teacher/course-preview/course-preview.component').then(
            (m) => m.CoursePreviewComponent,
          ),
      },
      {
        path: 'teacher/courses/:id/students',
        canActivate: [authGuard, roleGuard('TEACHER')],
        loadComponent: () =>
          import('./features/teacher/course-students/course-students.component').then(
            (m) => m.CourseStudentsComponent,
          ),
      },
      {
        path: 'admin',
        canActivate: [authGuard, roleGuard('ADMIN')],
        loadComponent: () =>
          import('./features/admin/dashboard/dashboard.component').then(
            (m) => m.AdminDashboardComponent,
          ),
      },
      {
        path: 'admin/users',
        canActivate: [authGuard, roleGuard('ADMIN')],
        loadComponent: () =>
          import('./features/admin/users/users.component').then((m) => m.AdminUsersComponent),
      },
      {
        path: 'admin/moderation',
        canActivate: [authGuard, roleGuard('ADMIN')],
        loadComponent: () =>
          import('./features/admin/moderation/moderation.component').then(
            (m) => m.AdminModerationComponent,
          ),
      },
      {
        path: 'admin/transactions',
        canActivate: [authGuard, roleGuard('ADMIN')],
        loadComponent: () =>
          import('./features/admin/transactions/transactions.component').then(
            (m) => m.AdminTransactionsComponent,
          ),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
