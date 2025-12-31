import { Component, inject, ViewChild, signal } from '@angular/core';
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
import { SystemPromptDialogComponent } from '../features/settings/system-prompt-dialog.component';
import { AdvancedLLMSettingsDialogComponent } from '../features/settings/advanced-llm-settings-dialog.component';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [RouterOutlet, CommonModule, MatToolbarModule, MatButtonModule, MatIconModule, MatMenuModule, MatDividerModule, ConfigPopoverComponent],
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
      background: rgb(14 26 53);
      color: white;
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
      color: #00CED1;
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
      color: rgba(255, 255, 255, 0.85);
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
        color: rgba(255, 255, 255, 0.9);
      }
    }

    .config-button {
      background: rgba(255, 255, 255, 0.1) !important;
      color: white !important;
      border: 1px solid rgba(255, 255, 255, 0.2) !important;
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
        color: white !important;
        cursor: pointer !important;
        transition: transform 0.3s ease;
        margin: 0 !important;
      }
      
      &:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
        
        ::ng-deep .mat-icon {
          transform: rotate(90deg);
        }
      }
    }

    .logout-button {
      background: rgba(255, 255, 255, 0.2) !important;
      color: white !important;
      border: 1px solid rgba(255, 255, 255, 0.4) !important;
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
        background: rgba(255, 255, 255, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.6) !important;
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
export class MainLayoutComponent {
  authService = inject(AuthService);
  dialog = inject(MatDialog);
  
  @ViewChild('configPopover') configPopover!: ConfigPopoverComponent;

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

  logout() {
    this.authService.logout();
  }
}

