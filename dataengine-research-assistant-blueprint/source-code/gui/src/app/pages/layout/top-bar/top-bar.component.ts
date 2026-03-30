import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatIcon } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { UserLogoComponent } from '../../../features/shared/components/user-logo/user-logo.component';
import { AppStoreService } from '../../../features/shared/services/app-store.service';
import { SystemPromptService } from '../../../features/shared/services/system-prompt.service';
import { SystemPromptDialogComponent } from '../../../features/shared/components/system-prompt-dialog/system-prompt-dialog.component';

@Component({
  selector: 'app-top-bar',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatIcon,
    MatTooltipModule,
    MatMenuModule,
    MatDialogModule,
    UserLogoComponent,
  ],
  templateUrl: './top-bar.component.html',
  styleUrl: './top-bar.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TopBarComponent {
  private appStoreService = inject(AppStoreService);
  private dialog = inject(MatDialog);
  promptService = inject(SystemPromptService);

  sidebarOpen = computed(() => this.appStoreService.sidebarOpen());

  toggleSidebar(): void {
    this.appStoreService.toggleSidebar();
  }

  onLogoClick(): void {
    this.appStoreService.closeSidebar();
  }

  onNewChat(): void {
    this.appStoreService.closeSidebar();
  }

  toggleDeepResearch(): void {
    this.promptService.loadSystemPrompt();
    this.promptService.toggleDeepResearch();
  }

  openSystemPrompt(): void {
    this.promptService.loadSystemPrompt();
    this.dialog.open(SystemPromptDialogComponent, {
      width: '600px',
      maxWidth: '90vw',
      panelClass: 'system-prompt-dialog-panel',
      backdropClass: 'system-prompt-dialog-backdrop',
      autoFocus: 'textarea',
    });
  }
}