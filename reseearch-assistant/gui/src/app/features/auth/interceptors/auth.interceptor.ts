import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { SETTINGS } from '../../shared/settings';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);

  // Skip auth for login and auth exchange endpoints
  if (req.url.includes(`${SETTINGS.BASE_API_URL}/login`) || 
      req.url.includes(`${SETTINGS.BASE_API_URL}/auth/exchange-session`)) {
    return next(req);
  }

  const authToken = authService.token();
  
  // Debug logging
  if (!authToken) {
    console.warn('AuthInterceptor: No token found for request:', req.url);
    console.warn('AuthInterceptor: Current state:', {
      token: authToken,
      status: authService.status(),
      user: authService.user()
    });
  }
  
  const authReq = authToken ? req.clone({
    setHeaders: { Authorization: `Bearer ${authToken}` }
  }) : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        // Don't logout if we're in the middle of token exchange
        if (!req.url.includes(`${SETTINGS.BASE_API_URL}/auth/exchange-session`)) {
          authService.logout();
        }
      }
      return throwError(() => error);
    })
  );
};
