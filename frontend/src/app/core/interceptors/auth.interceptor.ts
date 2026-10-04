import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';

import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const token = auth.accessToken();

  const isAuthEndpoint =
    req.url.includes('/auth/token/') || req.url.includes('/auth/register/');

  const authReq =
    token && !isAuthEndpoint
      ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status !== 401 || isAuthEndpoint || req.url.includes('/auth/token/refresh/')) {
        return throwError(() => error);
      }

      return auth.refreshAccessToken().pipe(
        switchMap((access) =>
          next(
            req.clone({
              setHeaders: { Authorization: `Bearer ${access}` },
            }),
          ),
        ),
        catchError(() => {
          // Invalid/expired session: clear quietly and retry as anonymous
          // so public endpoints (catalog) still work.
          auth.clearSession();
          return next(req.clone({ headers: req.headers.delete('Authorization') }));
        }),
      );
    }),
  );
};
