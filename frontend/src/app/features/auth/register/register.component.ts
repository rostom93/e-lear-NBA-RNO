import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

function passwordsMatch(group: AbstractControl): ValidationErrors | null {
  const password = group.get('password')?.value;
  const confirm = group.get('confirm')?.value;
  return password && confirm && password !== confirm ? { mismatch: true } : null;
}

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule, RouterLink, TranslatePipe],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly submitting = signal(false);
  readonly error = signal(false);
  readonly errorDetail = signal('');

  readonly form = this.fb.nonNullable.group(
    {
      first_name: [''],
      last_name: [''],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirm: ['', [Validators.required]],
    },
    { validators: passwordsMatch },
  );

  submit(): void {
    this.error.set(false);
    this.errorDetail.set('');

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const { first_name, last_name, email, password } = this.form.getRawValue();
    this.submitting.set(true);

    this.auth
      .registerAndLogin({
        email: email.trim(),
        password,
        first_name: first_name.trim(),
        last_name: last_name.trim(),
      })
      .subscribe({
        next: (user) => {
          this.submitting.set(false);
          void this.router.navigateByUrl(this.auth.dashboardRouteForRole(user.role));
        },
        error: (err: unknown) => {
          this.submitting.set(false);
          this.error.set(true);
          this.errorDetail.set(this.extractApiError(err));
        },
      });
  }

  private extractApiError(err: unknown): string {
    if (!(err instanceof HttpErrorResponse) || !err.error || typeof err.error !== 'object') {
      return '';
    }
    const chunks: string[] = [];
    for (const value of Object.values(err.error as Record<string, unknown>)) {
      if (typeof value === 'string') {
        chunks.push(value);
      } else if (Array.isArray(value)) {
        chunks.push(...value.filter((item): item is string => typeof item === 'string'));
      }
    }
    return chunks.slice(0, 3).join(' · ');
  }
}
