import { ChangeDetectionStrategy, Component, inject, computed } from '@angular/core';
import { AuthService } from '../../../auth/services/auth.service';

@Component({
  selector: 'app-greeting-message',
  standalone: true,
  template: `
    <div class="greeting">
      <h1 class="greeting__title">
        Hi, How can I help you today?
      </h1>
    </div>
  `,
  styles: [`
    .greeting {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 1.5rem;

      &__title {
        text-align: center;
        font-size: 2rem;
        font-weight: 600;
        color: #E8EBEC;
        line-height: 1.25;
        margin: 0;
      }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class GreetingMessageComponent {
  private readonly authService = inject(AuthService);

  username = computed(() => this.authService.user() || 'there');
}
