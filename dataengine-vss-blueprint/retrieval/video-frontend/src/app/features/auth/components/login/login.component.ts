import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { NgOptimizedImage } from '@angular/common';
import { MatFormField, MatLabel, MatSuffix } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinner } from '@angular/material/progress-spinner';
import { MatButton, MatIconButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    FormsModule,
    NgOptimizedImage,
    MatFormField,
    MatLabel,
    MatSuffix,
    MatInputModule,
    MatProgressSpinner,
    MatButton,
    MatIconButton,
    MatIcon
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class LoginComponent {
  fb = inject(FormBuilder);
  authService = inject(AuthService);

  form = this.fb.group({
    username: [localStorage.getItem('cached_username') || '', Validators.required],
    secretKey: ['', Validators.required]
  });
  
  // Secret key visibility toggle
  hideSecretKey = signal(true);

  onLogin() {
    if (this.form.valid) {
      const { username, secretKey } = this.form.value;
      if (username && secretKey) {
        localStorage.setItem('cached_username', username);
        this.authService.login(username, secretKey);
      }
    }
  }
}

