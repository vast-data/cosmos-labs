import { ChangeDetectionStrategy, Component, inject, OnInit } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { SETTINGS } from '../../../shared/settings';
import { NgOptimizedImage } from '@angular/common';
import { MatFormField } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinner } from '@angular/material/progress-spinner';
import {
    InputContainerComponent
} from '../../../shared/components/form-elements/input-container/input-container.component';

@Component({
  selector: 'app-login',
  standalone: true,
    imports: [ReactiveFormsModule, FormsModule, NgOptimizedImage, MatFormField, MatInputModule, MatProgressSpinner, InputContainerComponent],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class LoginComponent implements OnInit {
  fb = inject(FormBuilder);
  route = inject(ActivatedRoute);
  router = inject(Router);

  form = this.fb.group({
    username: ['', Validators.required],
    password: ['', Validators.required]
  });

  authService = inject(AuthService);

  ngOnInit() {
    // Check if already logged in
    if (this.authService.token()) {
      this.router.navigate([SETTINGS.DEFAULT_URL]);
      return;
    }

    // Check for Azure AD callback token or session_id in URL
    this.route.queryParams.subscribe(params => {
      const token = params['token'];
      const sessionId = params['session_id'];
      const error = params['error'];
      const provider = params['provider'];
      
      if (error) {
        // Handle error from Azure AD
        this.authService.state.update((state) => ({
          ...state,
          status: 'error',
          error: error === 'callback_failed' ? 'Azure AD authentication failed' : error
        }));
        // Clean URL
        this.router.navigate(['/login'], { replaceUrl: true, queryParams: {} });
      } else if (sessionId && provider === 'azuread') {
        // Exchange session_id for token (to avoid URL length limits)
        this.authService.exchangeSessionToken(sessionId);
      } else if (token && provider === 'azuread') {
        // Handle Azure AD token directly (fallback for shorter tokens)
        this.authService.loginWithToken(token);
      }
    });
  }

  onLogin() {
    const { username, password } = this.form.value;
    if (username && password) {
      this.authService.login(username, password);
    } else {
      this.authService.login('null', 'null', {});
    }
  }

  onAzureAdLogin() {
    // Check if already logged in
    if (this.authService.token()) {
      // Already logged in, navigate to default page
      this.router.navigate([SETTINGS.DEFAULT_URL]);
      return;
    }
    // Redirect to Azure AD login endpoint
    window.location.href = '/api/auth/login/nvlogin';
  }
}
