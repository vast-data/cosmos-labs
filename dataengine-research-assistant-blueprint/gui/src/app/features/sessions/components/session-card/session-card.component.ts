import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Session } from '../../../shared/models/sessions.model';
import { RouterModule } from '@angular/router';
import { AppStoreService } from '../../../shared/services/app-store.service';

@Component({
  selector: 'app-session-card',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './session-card.component.html',
  styleUrls: ['./session-card.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SessionCardComponent {
  private appStoreService = inject(AppStoreService);

  session = input.required<Session>();
  className = input<string>('');

  get sessionTitle(): string {
    return this.session().summary?.title || 'Untitled Session';
  }

  onSessionClick(): void {
    this.appStoreService.closeSidebar();
  }
}
