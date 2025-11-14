import { Component, inject, ViewChild, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from '../features/auth/services/auth.service';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialog } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { ConfigPopoverComponent } from '../features/config/config-popover.component';
import { StreamingConfigComponent } from '../features/streaming/streaming-config.component';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [RouterOutlet, CommonModule, MatToolbarModule, MatButtonModule, MatIconModule, MatMenuModule, ConfigPopoverComponent],
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
      background: linear-gradient(135deg, #0047AB 0%, #002766 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
      position: sticky;
      top: 0;
      z-index: 9999;
      min-height: 80px;
      height: 80px;
      padding: 0 2rem 0 1rem;
      display: flex !important;
      align-items: center;
      gap: 1.5rem;
      width: 100%;
      transition: all 0.3s ease;
      cursor: default !important;
      user-select: none !important;
      -webkit-user-select: none !important;
      -moz-user-select: none !important;
      -ms-user-select: none !important;
      
      &:hover {
        box-shadow: 0 6px 16px rgba(0, 71, 171, 0.35);
        transform: translateY(-1px);
      }
      
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
      height: 25px;
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
      font-size: 1.275rem;
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
      font-size: 0.75rem;
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
      min-height: calc(100vh - 80px);
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

  logout() {
    this.authService.logout();
  }
}

