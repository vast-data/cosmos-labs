import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { BatchSyncService } from '../../shared/services/batch-sync.service';
import { interval } from 'rxjs';

@Component({
  selector: 'app-batch-sync-progress-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="progress-dialog">
      <div class="dialog-header">
        <mat-icon class="header-icon">sync</mat-icon>
        <h2>Batch Sync Progress</h2>
        <button mat-icon-button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-content">
        @if (status()) {
          <div class="progress-info">
            <div class="status-row">
              <span class="label">Status:</span>
              <span class="value" [class.running]="status()?.status === 'running'" 
                    [class.completed]="status()?.status === 'completed'"
                    [class.failed]="status()?.status === 'failed'">
                {{ status()?.status?.toUpperCase() }}
              </span>
            </div>

            <div class="progress-row">
              <span class="label">Progress:</span>
              <span class="value">{{ status()?.completed_files || 0 }} / {{ status()?.total_files || 0 }} files</span>
            </div>

            <div class="destination-row">
              <span class="label">Source:</span>
              <span class="value">s3://{{ status()?.source_bucket || 'N/A' }}/{{ status()?.source_prefix || '' }}</span>
            </div>

            <div class="destination-row">
              <span class="label">Destination:</span>
              <span class="value dest-value">s3://{{ status()?.dest_bucket || 'N/A' }}</span>
            </div>

            <mat-progress-bar 
              mode="determinate" 
              [value]="progressPercentage()"
              [color]="status()?.status === 'running' ? 'primary' : (status()?.status === 'completed' ? 'primary' : 'warn')">
            </mat-progress-bar>

            <div class="stats-row">
              <div class="stat-item">
                <mat-icon>check_circle</mat-icon>
                <span>Completed: {{ status()?.completed_files || 0 }}</span>
              </div>
              <div class="stat-item">
                <mat-icon>error</mat-icon>
                <span>Failed: {{ status()?.failed_files || 0 }}</span>
              </div>
            </div>

            @if (status()?.current_file) {
              <div class="current-file">
                <mat-icon>file_copy</mat-icon>
                <span>Current: {{ status()?.current_file }}</span>
              </div>
            }

            @if (status()?.failed_file_list && status()?.failed_file_list.length > 0) {
              <div class="failed-files">
                <h4>Failed Files:</h4>
                <ul>
                  @for (file of status()?.failed_file_list; track file.source_key) {
                    <li>{{ file.source_key }} - {{ file.error }}</li>
                  }
                </ul>
              </div>
            }

            <div class="time-info">
              <div class="time-item">
                <span class="label">Started:</span>
                <span class="value">{{ formatTime(status()?.start_time) }}</span>
              </div>
              @if (status()?.end_time) {
                <div class="time-item">
                  <span class="label">Completed:</span>
                  <span class="value">{{ formatTime(status()?.end_time) }}</span>
                </div>
              }
            </div>
          </div>
        } @else {
          <div class="no-status">
            <mat-icon>info</mat-icon>
            <p>No active batch sync job</p>
          </div>
        }
      </div>

      <div class="dialog-actions">
        <button mat-button (click)="close()">Close</button>
        @if (status()?.status === 'running') {
          <button mat-raised-button color="warn" (click)="stop()" [disabled]="stopping()">
            @if (stopping()) {
              <mat-spinner diameter="20"></mat-spinner>
            } @else {
              <mat-icon>stop</mat-icon>
            }
            <span>Stop</span>
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
      background: linear-gradient(135deg, #0A0A1E 0%, #15152E 100%);
      color: white;
    }

    .dialog-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1.5rem 1.5rem 1rem 1.5rem;

      .header-icon {
        font-size: 28px;
        width: 28px;
        height: 28px;
        color: #00CED1;
      }

      h2 {
        flex: 1;
        margin: 0;
        font-size: 1.25rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.95);
      }

      .close-btn {
        color: rgba(255, 255, 255, 0.7);
        &:hover {
          color: white;
          background: rgba(255, 255, 255, 0.1);
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

    .status-row, .progress-row, .destination-row {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .label {
        color: rgba(255, 255, 255, 0.7);
      }

      .value {
        font-weight: 600;
        color: #00CED1;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        text-align: right;
        word-break: break-word;
        max-width: 60%;

        &.dest-value {
          color: #06ffa5;
          font-weight: 700;
        }

        &.running {
          color: #00CED1;
        }

        &.completed {
          color: #06ffa5;
        }

        &.failed {
          color: #ef4444;
        }
      }
    }

    mat-progress-bar {
      height: 8px;
      border-radius: 4px;
    }

    .stats-row {
      display: flex;
      gap: 2rem;

      .stat-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: rgba(255, 255, 255, 0.9);

        mat-icon {
          font-size: 18px;
          width: 18px;
          height: 18px;
        }
      }
    }

    .current-file {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem;
      background: rgba(0, 71, 171, 0.1);
      border-radius: 8px;
      color: rgba(255, 255, 255, 0.8);
      font-size: 0.9rem;

      mat-icon {
        color: #00CED1;
      }
    }

    .failed-files {
      margin-top: 1rem;
      padding: 1rem;
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.3);
      border-radius: 8px;

      h4 {
        margin: 0 0 0.5rem 0;
        color: #ef4444;
      }

      ul {
        margin: 0;
        padding-left: 1.5rem;
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.85rem;

        li {
          margin-bottom: 0.25rem;
        }
      }
    }

    .time-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);

      .time-item {
        display: flex;
        justify-content: space-between;

        .label {
          color: rgba(255, 255, 255, 0.7);
        }

        .value {
          color: rgba(255, 255, 255, 0.9);
        }
      }
    }

    .no-status {
      text-align: center;
      padding: 2rem;
      color: rgba(255, 255, 255, 0.7);

      mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        color: rgba(255, 255, 255, 0.5);
        margin-bottom: 1rem;
      }
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
      padding: 1rem 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);

      button {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer !important;
      }

      .mat-mdc-raised-button:not([color="warn"]) {
        background: linear-gradient(135deg, #0047AB 0%, #002766 100%) !important;
        color: white !important;
        
        &:hover:not([disabled]) {
          background: linear-gradient(135deg, #0056D6 0%, #0047AB 100%) !important;
          box-shadow: 0 4px 12px rgba(0, 71, 171, 0.4);
        }
      }
    }
  `]
})
export class BatchSyncProgressDialogComponent implements OnInit, OnDestroy {
  private dialogRef = inject(MatDialogRef<BatchSyncProgressDialogComponent>);
  private batchSyncService = inject(BatchSyncService);
  data = inject(MAT_DIALOG_DATA);

  status = signal<any>(null);
  stopping = signal(false);
  private refreshInterval: any;

  ngOnInit() {
    this.status.set(this.data);
    
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

  progressPercentage(): number {
    const s = this.status();
    if (!s || !s.total_files || s.total_files === 0) return 0;
    return (s.completed_files / s.total_files) * 100;
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
    this.batchSyncService.getStatus().subscribe({
      next: (result) => {
        if (result.success && result.status) {
          this.status.set(result.status);
        }
      },
      error: () => {
        // Ignore errors, keep showing current status
      }
    });
  }

  stop() {
    this.stopping.set(true);
    this.batchSyncService.stop().subscribe({
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

