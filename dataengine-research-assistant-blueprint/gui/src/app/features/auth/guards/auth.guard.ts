import { CanActivateFn, Router, ActivatedRouteSnapshot } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Check if there's a session_id in query params (Azure AD callback)
  const sessionId = route.queryParams['session_id'];
  const provider = route.queryParams['provider'];
  
  // If we have a session_id from Azure AD callback, allow access
  // The AppLayoutComponent will handle the token exchange
  if (sessionId && provider === 'azuread') {
    return true;
  }

  // Otherwise, check for existing token
  if (!authService.token()) {
    router.navigate(['/login']);
    return false;
  }
  return true;
};
