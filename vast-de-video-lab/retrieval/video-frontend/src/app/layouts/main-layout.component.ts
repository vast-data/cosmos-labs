import { Component, inject, ViewChild, signal, OnInit, OnDestroy } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from '../features/auth/services/auth.service';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialog } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { ConfigPopoverComponent } from '../features/config/config-popover.component';
import { StreamingConfigComponent } from '../features/streaming/streaming-config.component';
import { BatchSyncDialogComponent } from '../features/batch-sync/batch-sync-dialog.component';
import { BatchSyncProgressDialogComponent } from '../features/batch-sync/batch-sync-progress-dialog.component';
import { StreamingProgressDialogComponent } from '../features/streaming/streaming-progress-dialog.component';
import { SystemPromptDialogComponent } from '../features/settings/system-prompt-dialog.component';
import { AdvancedLLMSettingsDialogComponent } from '../features/settings/advanced-llm-settings-dialog.component';
import { BatchSyncService } from '../shared/services/batch-sync.service';
import { StreamingService } from '../shared/services/streaming.service';
import { ThemeService } from '../shared/services/theme.service';
import { interval } from 'rxjs';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [RouterOutlet, CommonModule, MatToolbarModule, MatButtonModule, MatIconModule, MatMenuModule, MatDividerModule, MatTooltipModule, ConfigPopoverComponent],
  template: `
    <mat-toolbar class="app-toolbar">
      <img src="assets/vast_logo.svg" alt="VAST" class="logo">
      <div class="title-container">
        <span class="main-title">DataEngine</span>
        <span class="subtitle">Video Reasoning Lab</span>
      </div>
      <span class="spacer"></span>
      <div class="user-info">
        <mat-icon class="user-icon">account_circle</mat-icon>
        <span>{{ authService.user() || 'User' }}</span>
      </div>
      @if (hasActiveStreaming()) {
        <button mat-icon-button 
                class="streaming-indicator" 
                [matTooltip]="streamingTooltip()"
                (click)="openStreamingProgress()">
          <mat-icon class="streaming-icon">live_tv</mat-icon>
        </button>
      }
      @if (hasActiveBatchSync()) {
        <button mat-icon-button 
                class="batch-sync-indicator" 
                [matTooltip]="batchSyncTooltip()"
                (click)="openBatchSyncProgress()">
          <mat-icon class="sync-icon">sync</mat-icon>
          <span class="sync-badge">{{ batchSyncProgress()?.completed_files || 0 }}/{{ batchSyncProgress()?.total_files || 0 }}</span>
        </button>
      }
      <button mat-icon-button 
              class="theme-toggle-button" 
              [matTooltip]="themeService.isDark() ? 'Switch to light mode' : 'Switch to dark mode'"
              (click)="themeService.toggleTheme()">
        <mat-icon>{{ themeService.isDark() ? 'light_mode' : 'dark_mode' }}</mat-icon>
      </button>
      <button mat-icon-button class="config-button" [matMenuTriggerFor]="configMenu">
        <mat-icon>settings</mat-icon>
      </button>
      <mat-menu #configMenu="matMenu" class="config-menu" xPosition="before" yPosition="below">
        <button mat-menu-item (click)="openBackendConfig()">
          <mat-icon>code</mat-icon>
          <span>Show Backend Config</span>
        </button>
        <button mat-menu-item (click)="openStreamingConfig()">
          <mat-icon>video_settings</mat-icon>
          <span>Configure Video Streaming</span>
        </button>
        <button mat-menu-item (click)="openBatchSyncDialog()">
          <mat-icon>sync</mat-icon>
          <span>S3 Batch Video Sync</span>
        </button>
        <mat-divider></mat-divider>
        <button mat-menu-item (click)="openSystemPromptConfig()">
          <mat-icon>psychology</mat-icon>
          <span>LLM System Prompt</span>
        </button>
        <button mat-menu-item (click)="openAdvancedLLMSettings()">
          <mat-icon>tune</mat-icon>
          <span>Advanced LLM Settings</span>
        </button>
      </mat-menu>
      <button mat-raised-button class="logout-button" (click)="logout()">
        <mat-icon>logout</mat-icon>
        <span>Logout</span>
      </button>
    </mat-toolbar>

    <div class="app-content">
      <router-outlet></router-outlet>
    </div>

    <app-config-popover #configPopover></app-config-popover>
  `,
  styles: [`
    .app-toolbar {
      background: var(--bg-toolbar);
      color: var(--text-primary);
      transition: background 0.3s ease, color 0.3s ease;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
      position: sticky;
      top: 0;
      z-index: 9999;
      min-height: 92px;
      height: 92px;
      padding: 0 2rem 0 1rem;
      display: flex !important;
      align-items: center;
      gap: 1.5rem;
      width: 100%;
      cursor: default !important;
      user-select: none !important;
      -webkit-user-select: none !important;
      -moz-user-select: none !important;
      -ms-user-select: none !important;
      
      // Prevent any text cursor in toolbar
      * {
        cursor: default !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
      }
      
      // Override for logout button only
      .logout-button,
      .logout-button * {
        cursor: pointer !important;
        user-select: none !important;
      }
    }

    .logo {
      height: 29px;
      width: auto;
      object-fit: contain;
      flex-shrink: 0;
      margin-left: 0;
      cursor: default !important;
      user-select: none !important;
      pointer-events: none !important;
      filter: brightness(0) invert(1);
      transition: filter 0.3s ease;
    }
    
    :host-context([data-theme="light"]) .logo,
    [data-theme="light"] .logo {
      filter: brightness(0) invert(0);
    }

    .title-container {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
      flex-shrink: 0;
      cursor: default !important;
      user-select: none !important;
      pointer-events: none !important;
    }

    .main-title {
      font-size: 1.47rem;
      font-weight: 700;
      color: var(--accent-primary);
      white-space: nowrap;
      line-height: 1.2;
      letter-spacing: 0.5px;
      cursor: default !important;
      user-select: none !important;
      pointer-events: none !important;
    }

    .subtitle {
      font-size: 0.86rem;
      font-weight: 400;
      color: var(--text-secondary);
      white-space: nowrap;
      line-height: 1;
      letter-spacing: 0.3px;
      cursor: default !important;
      user-select: none !important;
      pointer-events: none !important;
    }

    .spacer {
      flex: 1;
    }

    .user-info {
      margin-right: 0.5rem;
      opacity: 0.9;
      font-size: 0.95rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      
      .user-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
        color: var(--text-secondary);
      }
    }

    .batch-sync-indicator {
      position: relative;
      margin-right: 0.5rem;
      background: rgba(0, 206, 209, 0.2) !important;
      border: 1px solid rgba(0, 206, 209, 0.4) !important;
      cursor: pointer !important;

      .sync-icon {
        color: var(--accent-primary) !important;
        animation: spin 2s linear infinite;
      }

      .sync-badge {
        position: absolute;
        top: -4px;
        right: -4px;
        background: var(--accent-primary);
        color: var(--bg-primary);
        font-size: 0.65rem;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 10px;
        min-width: 30px;
        text-align: center;
      }

      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
    }

    .streaming-indicator {
      position: relative;
      color: #FF6B6B;
      margin-right: 0.5rem;
      
      .streaming-icon {
        animation: pulse 1.5s ease-in-out infinite;
      }

      @keyframes pulse {
        0%, 100% {
          opacity: 1;
          transform: scale(1);
        }
        50% {
          opacity: 0.7;
          transform: scale(1.1);
        }
      }
      
      &:hover {
        color: #FF8E8E;
      }
    }

    .theme-toggle-button {
      background: rgba(0, 206, 209, 0.1) !important;
      color: var(--accent-primary) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 50% !important;
      width: 38px !important;
      height: 38px !important;
      min-width: 38px !important;
      cursor: pointer !important;
      transition: all 0.3s ease;
      margin-right: 0.5rem;
      padding: 0 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      
      ::ng-deep .mat-mdc-button-touch-target {
        display: none !important;
      }
      
      ::ng-deep .mat-icon {
        font-size: 20px !important;
        width: 20px !important;
        height: 20px !important;
        line-height: 20px !important;
        color: var(--accent-primary) !important;
        cursor: pointer !important;
        transition: transform 0.3s ease;
        margin: 0 !important;
      }
      
      &:hover {
        background: rgba(0, 206, 209, 0.2) !important;
        border-color: var(--border-hover) !important;
        transform: scale(1.05);
        
        ::ng-deep .mat-icon {
          transform: rotate(15deg);
        }
      }
      
      &:active {
        transform: scale(0.95);
      }
    }

    .config-button {
      background: var(--bg-card) !important;
      color: var(--text-primary) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 50% !important;
      width: 38px !important;
      height: 38px !important;
      min-width: 38px !important;
      cursor: pointer !important;
      transition: all 0.3s ease;
      margin-right: 1rem;
      padding: 0 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      
      ::ng-deep .mat-mdc-button-touch-target {
        display: none !important;
      }
      
      ::ng-deep .mat-icon {
        font-size: 20px !important;
        width: 20px !important;
        height: 20px !important;
        line-height: 20px !important;
        color: var(--text-primary) !important;
        cursor: pointer !important;
        transition: transform 0.3s ease;
        margin: 0 !important;
      }
      
      &:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--border-hover) !important;
        
        ::ng-deep .mat-icon {
          transform: rotate(90deg);
        }
      }
    }

    .logout-button {
      background: var(--bg-card) !important;
      color: var(--text-primary) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 4px !important;
      display: flex !important;
      align-items: center;
      gap: 0.5rem;
      padding: 0 1.25rem !important;
      height: 38px;
      transition: all 0.2s ease;
      font-weight: 500;
      cursor: pointer !important;
      
      * {
        cursor: pointer !important;
      }
      
      &:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--border-hover) !important;
      }
      
      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
        cursor: pointer !important;
      }
    }

    .app-content {
      min-height: calc(100vh - 92px);
      overflow: auto;
      padding-top: 1rem;
    }
  `]
})
export class MainLayoutComponent implements OnInit, OnDestroy {
  authService = inject(AuthService);
  dialog = inject(MatDialog);
  batchSyncService = inject(BatchSyncService);
  streamingService = inject(StreamingService);
  themeService = inject(ThemeService);
  
  @ViewChild('configPopover') configPopover!: ConfigPopoverComponent;

  hasActiveBatchSync = signal(false);
  batchSyncProgress = signal<any>(null);
  batchSyncTooltip = signal('No active batch sync');

  hasActiveStreaming = signal(false);
  streamingStatus = signal<any>(null);
  streamingTooltip = signal('No active streaming');

  private statusCheckInterval: any;

  ngOnInit() {
    // Check for active batch sync and streaming every 2 seconds
    this.statusCheckInterval = interval(2000).subscribe(() => {
      this.checkBatchSyncStatus();
      this.checkStreamingStatus();
    });
    this.checkBatchSyncStatus();
    this.checkStreamingStatus();
  }

  ngOnDestroy() {
    if (this.statusCheckInterval) {
      this.statusCheckInterval.unsubscribe();
    }
  }

  checkBatchSyncStatus() {
    this.batchSyncService.getStatus().subscribe({
      next: (result) => {
        if (result.success && result.status && result.status.status === 'running') {
          this.hasActiveBatchSync.set(true);
          this.batchSyncProgress.set(result.status);
          this.batchSyncTooltip.set(
            `Batch sync in progress: ${result.status.completed_files}/${result.status.total_files} files`
          );
        } else {
          this.hasActiveBatchSync.set(false);
          this.batchSyncProgress.set(null);
        }
      },
      error: () => {
        this.hasActiveBatchSync.set(false);
      }
    });
  }

  checkStreamingStatus() {
    this.streamingService.getStatus().subscribe({
      next: (result) => {
        if (result.success && result.status && result.status.is_running) {
          this.hasActiveStreaming.set(true);
          this.streamingStatus.set(result.status);
          const config = result.status.current_config || {};
          this.streamingTooltip.set(
            `Live streaming active: ${config.name || 'Stream'}`
          );
        } else {
          this.hasActiveStreaming.set(false);
          this.streamingStatus.set(null);
        }
      },
      error: () => {
        this.hasActiveStreaming.set(false);
      }
    });
  }

  openStreamingProgress() {
    // Pass the full status structure that the dialog expects
    const status = this.streamingStatus();
    const dialogData = status ? {
      success: true,
      status: status,
      timestamp: new Date().toISOString()
    } : null;
    
    this.dialog.open(StreamingProgressDialogComponent, {
      width: '500px',
      maxHeight: '80vh',
      panelClass: 'streaming-progress-dialog-container',
      disableClose: false,
      data: dialogData
    });
  }

  openBackendConfig() {
    this.configPopover.open();
  }

  openStreamingConfig() {
    this.dialog.open(StreamingConfigComponent, {
      width: '600px',
      maxHeight: '80vh',
      panelClass: 'streaming-dialog-container',
      disableClose: false
    });
  }

  openSystemPromptConfig() {
    this.dialog.open(SystemPromptDialogComponent, {
      width: '650px',
      maxHeight: '85vh',
      panelClass: 'system-prompt-dialog-container',
      disableClose: false
    });
  }

  openAdvancedLLMSettings() {
    this.dialog.open(AdvancedLLMSettingsDialogComponent, {
      width: '550px',
      maxHeight: '85vh',
      panelClass: 'advanced-llm-settings-dialog-container',
      disableClose: false
    });
  }

  openBatchSyncDialog() {
    const dialogRef = this.dialog.open(BatchSyncDialogComponent, {
      width: '700px',
      maxHeight: '90vh',
      panelClass: 'batch-sync-dialog-container',
      disableClose: false
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result?.started) {
        // Refresh status check
        this.checkBatchSyncStatus();
      }
    });
  }

  openBatchSyncProgress() {
    const progress = this.batchSyncProgress();
    if (!progress) return;

    this.dialog.open(BatchSyncProgressDialogComponent, {
      width: '500px',
      maxHeight: '80vh',
      panelClass: 'batch-sync-progress-dialog-container',
      disableClose: false,
      data: progress
    });
  }

  logout() {
    // Switch to dark mode before logout to ensure login screen displays correctly
    this.themeService.setTheme('dark');
    this.authService.logout();
  }
}

