import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { AdminUser, AdminUserWrite } from '../../../core/models/admin.model';
import { UserRole } from '../../../core/models/user.model';
import { AdminService } from '../../../core/services/admin.service';
import { TranslationService } from '../../../core/services/translation.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-admin-users',
  imports: [ReactiveFormsModule, RouterLink, TranslatePipe],
  templateUrl: './users.component.html',
  styleUrl: './users.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminUsersComponent implements OnInit {
  private readonly adminApi = inject(AdminService);
  private readonly fb = inject(FormBuilder);
  private readonly i18n = inject(TranslationService);

  readonly users = signal<AdminUser[]>([]);
  readonly loading = signal(true);
  readonly error = signal(false);
  readonly message = signal<'saved' | 'error' | 'deleteError' | null>(null);
  readonly editingId = signal<number | null>(null);
  readonly saving = signal(false);
  readonly deletingId = signal<number | null>(null);

  readonly roles: UserRole[] = ['STUDENT', 'TEACHER', 'ADMIN'];

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    username: [''],
    first_name: [''],
    last_name: [''],
    role: this.fb.nonNullable.control<UserRole>('STUDENT'),
    credit_balance: [0, [Validators.required, Validators.min(0)]],
    is_active: [true],
    is_staff: [false],
    password: [''],
  });

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.error.set(false);
    this.adminApi.listUsers().subscribe({
      next: (users) => {
        this.users.set(users);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }

  startCreate(): void {
    this.editingId.set(null);
    this.message.set(null);
    this.form.reset({
      email: '',
      username: '',
      first_name: '',
      last_name: '',
      role: 'STUDENT',
      credit_balance: 0,
      is_active: true,
      is_staff: false,
      password: '',
    });
  }

  startEdit(user: AdminUser): void {
    this.editingId.set(user.id);
    this.message.set(null);
    this.form.reset({
      email: user.email,
      username: user.username,
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
      credit_balance: user.credit_balance,
      is_active: user.is_active,
      is_staff: user.is_staff,
      password: '',
    });
  }

  cancelEdit(): void {
    this.editingId.set(null);
    this.startCreate();
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const value = this.form.getRawValue();
    const editingId = this.editingId();
    this.saving.set(true);
    this.message.set(null);

    if (editingId === null) {
      if (!value.password) {
        this.form.controls.password.setErrors({ required: true });
        this.saving.set(false);
        return;
      }
      this.adminApi
        .createUser({
          email: value.email,
          username: value.username || undefined,
          first_name: value.first_name,
          last_name: value.last_name,
          role: value.role,
          credit_balance: value.credit_balance,
          is_active: value.is_active,
          is_staff: value.role === 'ADMIN' || value.is_staff,
          password: value.password,
        })
        .subscribe({
          next: () => {
            this.saving.set(false);
            this.message.set('saved');
            this.startCreate();
            this.reload();
          },
          error: () => {
            this.saving.set(false);
            this.message.set('error');
          },
        });
      return;
    }

    const payload: Partial<AdminUserWrite> = {
      email: value.email,
      username: value.username,
      first_name: value.first_name,
      last_name: value.last_name,
      role: value.role,
      credit_balance: value.credit_balance,
      is_active: value.is_active,
      is_staff: value.role === 'ADMIN' || value.is_staff,
    };
    if (value.password) {
      payload.password = value.password;
    }

    this.adminApi.updateUser(editingId, payload).subscribe({
      next: () => {
        this.saving.set(false);
        this.message.set('saved');
        this.cancelEdit();
        this.reload();
      },
      error: () => {
        this.saving.set(false);
        this.message.set('error');
      },
    });
  }

  remove(user: AdminUser): void {
    if (!confirm(this.i18n.t('admin.users.confirmDelete'))) {
      return;
    }
    this.deletingId.set(user.id);
    this.adminApi.deleteUser(user.id).subscribe({
      next: () => {
        this.deletingId.set(null);
        if (this.editingId() === user.id) {
          this.cancelEdit();
        }
      },
      error: () => {
        this.deletingId.set(null);
        this.message.set('deleteError');
      },
    });
  }

  displayName(user: AdminUser): string {
    const full = `${user.first_name} ${user.last_name}`.trim();
    return full || user.username || user.email;
  }

  roleLabel(role: UserRole): string {
    return this.i18n.t(`admin.role.${role}`);
  }
}
