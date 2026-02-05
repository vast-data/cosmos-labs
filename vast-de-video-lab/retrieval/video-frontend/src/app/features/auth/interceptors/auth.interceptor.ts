import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const token = authService.token();

  // Don't add token to login endpoint
  if (req.url.includes('/auth/login')) {
    return next(req);
  }

  // Add token to request if available
  const clonedReq = token 
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      })
    : req;

  // Handle response and catch 401 errors
  return next(clonedReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // If we get a 401 Unauthorized, the session has expired
      if (error.status === 401) {
        // Clear auth state without full page reload (we'll use router navigation)
        authService.logout(false);
        // Redirect to login page
        router.navigate(['/login']);
      }
      return throwError(() => error);
    })
  );
};

