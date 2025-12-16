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
    secretKey: ['', Validators.required],
    vastHost: [localStorage.getItem('cached_vast_vms') || '', Validators.required]
  });
  
  // Secret key visibility toggle
  hideSecretKey = signal(true);

  onLogin() {
    if (this.form.valid) {
      const { username, secretKey, vastHost } = this.form.value;
      if (username && secretKey && vastHost) {
        // Cache username and VMS for next time (but NOT secret key)
        localStorage.setItem('cached_username', username);
        localStorage.setItem('cached_vast_vms', vastHost);
        
        this.authService.login(username, secretKey, vastHost);
      }
    }
  }
}

