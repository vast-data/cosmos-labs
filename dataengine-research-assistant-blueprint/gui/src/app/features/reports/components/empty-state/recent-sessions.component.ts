import { ChangeDetectionStrategy, Component, inject, computed } from '@angular/core';
import { RouterModule } from '@angular/router';
import { SessionsService } from '../../../sessions/services/sessions.service';

@Component({
  selector: 'app-recent-sessions',
  standalone: true,
  imports: [RouterModule],
  template: `
    <div class="recent-sessions">
      <h2 class="recent-sessions__title">Dive Back In</h2>
      
      <div class="recent-sessions__list">
        @if (isLoading()) {
          @for (i of [1, 2, 3]; track i) {
            <div class="recent-sessions__skeleton"></div>
          }
        } @else if (recentSessions().length === 0) {
          <!-- Empty state - no sessions yet -->
        } @else {
          @for (session of recentSessions(); track session.session_id) {
            <a 
              class="recent-sessions__card" 
              [routerLink]="['/chat', session.session_id]"
            >
              <h3 class="recent-sessions__card-title">{{ getSessionTitle(session) }}</h3>
              <span class="recent-sessions__card-date">{{ formatSessionDate(session.updated_at) }}</span>
            </a>
          }
        }
      </div>
    </div>
  `,
  styles: [`
    .recent-sessions {
      width: 100%;
      max-width: 56rem;

      &__title {
        font-size: 1.125rem;
        font-weight: 600;
        line-height: 1.25;
        margin-bottom: 1.5rem;
        text-align: left;
        color: rgba(255, 255, 255, 0.6);
      }

      &__list {
        display: flex;
        align-items: center;
        gap: 1.25rem;
      }

      &__skeleton {
        width: 260px;
        height: 60px;
        background: #0F1A31;
        border: 1px solid #343E55;
        border-radius: 0.5rem;
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
      }

      &__card {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 0.75rem;
        background: #0F1A31;
        border: 1px solid #343E55;
        border-radius: 0.5rem;
        text-decoration: none;
        min-width: 260px;
        cursor: pointer;
        transition: background-color 0.2s ease, border-color 0.2s ease;

        &:hover {
          background: #1a2844;
          border-color: #4a5568;
        }
      }

      &__card-title {
        font-size: 0.875rem;
        line-height: .875rem;
        font-weight: 500;
        color: #E8EBEC;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      &__card-date {
        font-size: 0.875rem;
        line-height: .875rem;
        color: #C5CCCE;
      }
    }

    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.5;
      }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class RecentSessionsComponent {
  private readonly sessionsService = inject(SessionsService);

  isLoading = computed(() => this.sessionsService.isLoading());
  
  recentSessions = computed(() => {
    const sessions = this.sessionsService.sessions();
    return sessions.slice(0, 3);
  });

  getSessionTitle(session: { summary?: { title?: string } | null }): string {
    return session.summary?.title || 'Untitled Session';
  }

  formatSessionDate(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'short' });
    const day = date.getDate();
    const month = date.toLocaleDateString('en-US', { month: 'short' });
    return `${dayOfWeek} ${day} ${month}`;
  }
}
