import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { StreamingService } from '../../shared/services/streaming.service';
import { interval } from 'rxjs';

@Component({
  selector: 'app-streaming-progress-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="progress-dialog">
      <div class="dialog-header">
        <mat-icon class="header-icon">live_tv</mat-icon>
        <h2>Live Streaming Status</h2>
        <button mat-icon-button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-content">
        @if (status()) {
          <div class="progress-info">
            <div class="status-row">
              <span class="label">Status:</span>
              <span class="value" [class.running]="status()?.status?.is_running" 
                    [class.stopped]="!status()?.status?.is_running">
                {{ status()?.status?.is_running ? 'LIVE' : 'STOPPED' }}
              </span>
            </div>

            @if (status()?.status?.is_running && status()?.status?.current_config) {
              <div class="config-info">
                <div class="info-row">
                  <span class="label">Stream Name:</span>
                  <span class="value">{{ status()?.status?.current_config?.name || 'N/A' }}</span>
                </div>
                <div class="info-row">
                  <span class="label">YouTube URL:</span>
                  <span class="value url">{{ status()?.status?.current_config?.youtube_url || 'N/A' }}</span>
                </div>
                <div class="info-row">
                  <span class="label">Capture Interval:</span>
                  <span class="value">{{ status()?.status?.current_config?.capture_interval || 'N/A' }}s</span>
                </div>
                
                @if (status()?.status?.current_config?.camera_id || 
                     status()?.status?.current_config?.capture_type || 
                     status()?.status?.current_config?.neighborhood) {
                  <div class="metadata-section">
                    <h4>Stream Metadata</h4>
                    @if (status()?.status?.current_config?.camera_id) {
                      <div class="info-row">
                        <span class="label">Camera ID:</span>
                        <span class="value">{{ status()?.status?.current_config?.camera_id }}</span>
                      </div>
                    }
                    @if (status()?.status?.current_config?.capture_type) {
                      <div class="info-row">
                        <span class="label">Capture Type:</span>
                        <span class="value">{{ status()?.status?.current_config?.capture_type }}</span>
                      </div>
                    }
                    @if (status()?.status?.current_config?.neighborhood) {
                      <div class="info-row">
                        <span class="label">Neighborhood:</span>
                        <span class="value">{{ status()?.status?.current_config?.neighborhood }}</span>
                      </div>
                    }
                  </div>
                }
              </div>
            } @else {
              <div class="no-streaming">
                <mat-icon>info</mat-icon>
                <p>No active streaming session</p>
              </div>
            }

            <div class="time-info">
              <div class="time-item">
                <span class="label">Last Updated:</span>
                <span class="value">{{ formatTime(status()?.timestamp) }}</span>
              </div>
            </div>
          </div>
        } @else {
          <div class="no-status">
            <mat-icon>info</mat-icon>
            <p>No streaming status available</p>
          </div>
        }
      </div>

      <div class="dialog-actions">
        <button mat-button (click)="close()">Close</button>
        @if (status()?.status?.is_running) {
          <button mat-raised-button color="warn" (click)="stop()" [disabled]="stopping()">
            @if (stopping()) {
              <mat-spinner diameter="20"></mat-spinner>
            } @else {
              <mat-icon>stop</mat-icon>
            }
            <span>Stop Streaming</span>
          </button>
        }
        <button mat-raised-button (click)="refresh()">
          <mat-icon>refresh</mat-icon>
          <span>Refresh</span>
        </button>
      </div>
    </div>
  `,
  styles: [`
    .progress-dialog {
      width: 500px;
      background: var(--bg-card);
      color: var(--text-primary);
      transition: background 0.3s ease, color 0.3s ease;
    }

    .dialog-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1.5rem 1.5rem 1rem 1.5rem;
      border-bottom: 1px solid var(--border-color);
      transition: border-color 0.3s ease;

      .header-icon {
        font-size: 28px;
        width: 28px;
        height: 28px;
        color: #FF6B6B;
      }

      h2 {
        flex: 1;
        margin: 0;
        font-size: 1.25rem;
        font-weight: 500;
        color: var(--text-primary);
      }

      .close-btn {
        color: var(--text-secondary);
        &:hover {
          color: var(--text-primary);
          background: var(--bg-card-hover);
        }
      }
    }

    .dialog-content {
      padding: 0 1.5rem 1.5rem 1.5rem;
    }

    .progress-info {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .status-row, .info-row {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .label {
        color: var(--text-secondary);
      }

      .value {
        font-weight: 600;
        color: var(--accent-primary);
        text-align: right;
        word-break: break-word;
        max-width: 60%;

        &.url {
          font-size: 0.85rem;
          color: var(--text-secondary);
        }

        &.running {
          color: #FF6B6B;
        }

        &.stopped {
          color: var(--text-muted);
        }
      }
    }

    .config-info {
      margin-top: 1rem;
      padding: 1rem;
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      transition: background 0.3s ease, border-color 0.3s ease;
    }

    .metadata-section {
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border-color);
      transition: border-color 0.3s ease;

      h4 {
        margin: 0 0 0.75rem 0;
        color: var(--text-primary);
        font-size: 0.9rem;
        font-weight: 500;
      }
    }

    .no-streaming, .no-status {
      text-align: center;
      padding: 2rem;
      color: var(--text-secondary);

      mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        color: var(--text-muted);
        margin-bottom: 1rem;
      }
    }

    .time-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border-color);
      transition: border-color 0.3s ease;

      .time-item {
        display: flex;
        justify-content: space-between;

        .label {
          color: var(--text-secondary);
        }

        .value {
          color: var(--text-primary);
        }
      }
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
      padding: 1rem 1.5rem;
      border-top: 1px solid var(--border-color);
      transition: border-color 0.3s ease;

      button {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer !important;
      }

      /* Close button (mat-button) */
      .mat-mdc-button:not([color="warn"]) {
        background: #73c8fd !important; /* lightblue-400 */
        color: #0e1a35 !important; /* blue-900 - dark text for contrast */
        
        &:hover:not([disabled]) {
          background: #b7e3ff !important; /* lightblue-200 - lighter on hover */
          box-shadow: var(--shadow-hover);
        }
      }

      /* Refresh button (mat-raised-button) */
      .mat-mdc-raised-button:not([color="warn"]) {
        background: #73c8fd !important; /* lightblue-400 */
        color: #0e1a35 !important; /* blue-900 - dark text for contrast */
        
        &:hover:not([disabled]) {
          background: #b7e3ff !important; /* lightblue-200 - lighter on hover */
          box-shadow: var(--shadow-hover);
        }
      }
    }
  `]
})
export class StreamingProgressDialogComponent implements OnInit, OnDestroy {
  private dialogRef = inject(MatDialogRef<StreamingProgressDialogComponent>);
  private streamingService = inject(StreamingService);
  data = inject(MAT_DIALOG_DATA);

  status = signal<any>(null);
  stopping = signal(false);
  private refreshInterval: any;

  ngOnInit() {
    // Initialize with current data if available, otherwise fetch
    if (this.data) {
      // If data is just the status object, wrap it in the expected format
      if (this.data.is_running !== undefined) {
        this.status.set({
          success: true,
          status: this.data,
          timestamp: new Date().toISOString()
        });
      } else {
        this.status.set(this.data);
      }
    }
    
    // Always fetch fresh status on init
    this.refresh();
    
    // Auto-refresh every 2 seconds
    this.refreshInterval = interval(2000).subscribe(() => {
      this.refresh();
    });
  }

  ngOnDestroy() {
    if (this.refreshInterval) {
      this.refreshInterval.unsubscribe();
    }
  }

  formatTime(timeStr: string | null): string {
    if (!timeStr) return 'N/A';
    try {
      const date = new Date(timeStr);
      return date.toLocaleString();
    } catch {
      return timeStr;
    }
  }

  refresh() {
    this.streamingService.getStatus().subscribe({
      next: (result) => {
        if (result.success) {
          this.status.set(result);
          // Also update the main layout's status if dialog is open
          // This ensures the indicator stays in sync
        } else {
          // If streaming stopped, clear status
          this.status.set({
            success: true,
            status: { is_running: false },
            timestamp: new Date().toISOString()
          });
        }
      },
      error: () => {
        // Ignore errors, keep showing current status
      }
    });
  }

  stop() {
    this.stopping.set(true);
    this.streamingService.stop().subscribe({
      next: (result) => {
        this.stopping.set(false);
        if (result.success) {
          // Refresh status to show stopped state
          this.refresh();
        }
      },
      error: () => {
        this.stopping.set(false);
      }
    });
  }

  close() {
    this.dialogRef.close();
  }
}

