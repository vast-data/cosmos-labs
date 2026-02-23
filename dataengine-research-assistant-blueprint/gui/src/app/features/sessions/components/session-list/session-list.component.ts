import { ChangeDetectionStrategy, Component, inject, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SessionsService } from '../../services/sessions.service';
import { SessionCardComponent } from '../session-card/session-card.component';
import { Session } from '../../../shared/models/sessions.model';

@Component({
  selector: 'app-session-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    SessionCardComponent
  ],
  templateUrl: './session-list.component.html',
  styleUrls: ['./session-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SessionListComponent {
  private sessionsService = inject(SessionsService);

  searchQuery = signal('');
  isLoading = computed(() => this.sessionsService.isLoading());

  filteredSessions = computed(() => {
    const query = this.searchQuery().toLowerCase().trim();
    const sessions = this.sessionsService.sessions();

    if (!query) {
      return sessions;
    }

    return sessions.filter(session => {
      const title = session.summary?.title?.toLowerCase() ?? '';
      const description = session.summary?.description?.toLowerCase() ?? '';
      return title.includes(query) || description.includes(query);
    });
  });

  trackBySessionId(index: number, session: Session): string {
    return session.session_id;
  }
}
