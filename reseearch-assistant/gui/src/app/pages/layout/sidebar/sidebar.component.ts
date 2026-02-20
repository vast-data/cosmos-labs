import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatIcon } from '@angular/material/icon';
import { AppStoreService } from '../../../features/shared/services/app-store.service';
import { SessionListComponent } from '../../../features/sessions/components/session-list/session-list.component';

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

  sidebarOpen = computed(() => this.appStoreService.sidebarOpen());

  closeSidebar(): void {
    this.appStoreService.closeSidebar();
  }
}