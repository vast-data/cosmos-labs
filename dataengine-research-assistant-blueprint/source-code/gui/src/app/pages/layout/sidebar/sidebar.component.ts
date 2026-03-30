import { Component, computed, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatIcon } from '@angular/material/icon';
import { AppStoreService } from '../../../features/shared/services/app-store.service';
import { SessionListComponent } from '../../../features/sessions/components/session-list/session-list.component';
import { SessionsService } from '../../../features/sessions/services/sessions.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatIcon,
    SessionListComponent,
  ],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent {
  private appStoreService = inject(AppStoreService);
  private sessionsService = inject(SessionsService);

  sidebarOpen = computed(() => this.appStoreService.sidebarOpen());

  constructor() {
    effect(() => {
      if (this.sidebarOpen()) {
        this.sessionsService.loadSessions();
      }
    });
  }

  closeSidebar(): void {
    this.appStoreService.closeSidebar();
  }

  onNewConversation(): void {
    this.appStoreService.closeSidebar();
  }
}