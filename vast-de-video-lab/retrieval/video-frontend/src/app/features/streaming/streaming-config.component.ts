import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { StreamingService, StreamingStartRequest } from '../../shared/services/streaming.service';

@Component({
  selector: 'app-streaming-config',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatTabsModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="streaming-dialog">
      <div class="dialog-header">
        <mat-icon class="header-icon">video_settings</mat-icon>
        <h2>Video Streaming Configuration</h2>
        <button mat-icon-button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <mat-tab-group class="streaming-tabs" animationDuration="300ms">
        <!-- Tab 1: Check Status -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon>info</mat-icon>
            <span>Check Status</span>
          </ng-template>
          <div class="tab-content">
            <p class="tab-description">View the current streaming service status and configuration</p>
            
            <button mat-raised-button class="action-btn" (click)="checkStatus()" [disabled]="statusLoading()">
              @if (statusLoading()) {
                <mat-spinner diameter="20"></mat-spinner>
              } @else {
                <mat-icon>refresh</mat-icon>
              }
              <span>Check Streaming Status</span>
            </button>

            @if (statusResult()) {
              <div class="result-box" [class.success]="statusResult()?.success" [class.error]="!statusResult()?.success">
                <div class="result-header">
                  <mat-icon>{{ statusResult()?.success ? 'check_circle' : 'error' }}</mat-icon>
                  <span>Status Response</span>
                </div>
                <pre class="result-content">{{ formatJSON(statusResult()) }}</pre>
              </div>
            }
          </div>
        </mat-tab>

        <!-- Tab 2: Start Capture -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon>play_arrow</mat-icon>
            <span>Start Capture</span>
          </ng-template>
          <div class="tab-content">
            <p class="tab-description">Start capturing video from a YouTube stream to S3</p>
            
            <form [formGroup]="startForm" class="streaming-form">
              <mat-form-field appearance="outline">
                <mat-label>YouTube URL</mat-label>
                <input matInput formControlName="youtube_url" placeholder="https://www.youtube.com/watch?v=...">
                <mat-icon matSuffix>link</mat-icon>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>S3 Access Key</mat-label>
                <input matInput formControlName="access_key" placeholder="Enter S3 access key">
                <mat-icon matSuffix>vpn_key</mat-icon>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>S3 Secret Key</mat-label>
                <input matInput type="password" formControlName="secret_key" placeholder="Enter S3 secret key">
                <mat-icon matSuffix>lock</mat-icon>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>S3 Endpoint</mat-label>
                <input matInput formControlName="s3_endpoint" placeholder="http://your-s3-endpoint">
                <mat-icon matSuffix>cloud</mat-icon>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Bucket Name</mat-label>
                <input matInput formControlName="bucket_name" placeholder="your-bucket-name">
                <mat-icon matSuffix>folder</mat-icon>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Custom Name (prefix)</mat-label>
                <input matInput formControlName="name" placeholder="capture">
                <mat-icon matSuffix>label</mat-icon>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Capture Interval (seconds)</mat-label>
                <input matInput type="number" formControlName="capture_interval" placeholder="10">
                <mat-icon matSuffix>schedule</mat-icon>
              </mat-form-field>

              <!-- Metadata Section -->
              <div class="metadata-section">
                <h3 class="section-title">
                  <mat-icon>info</mat-icon>
                  <span>Stream Metadata (Optional)</span>
                </h3>
                <p class="section-description">These fields will be stored with each video segment for filtering and search</p>

                <mat-form-field appearance="outline">
                  <mat-label>Camera ID</mat-label>
                  <input matInput formControlName="camera_id" placeholder="e.g., CAM-001, manhattan-cam-1">
                  <mat-icon matSuffix>videocam</mat-icon>
                </mat-form-field>

                <mat-form-field appearance="outline">
                  <mat-label>Capture Type</mat-label>
                  <mat-select formControlName="capture_type">
                    <mat-option [value]="">-- Select Type --</mat-option>
                    <mat-option value="traffic">Traffic</mat-option>
                    <mat-option value="streets">Streets</mat-option>
                    <mat-option value="crowds">Crowds</mat-option>
                    <mat-option value="malls">Malls</mat-option>
                  </mat-select>
                  <mat-icon matSuffix>category</mat-icon>
                </mat-form-field>

                <mat-form-field appearance="outline">
                  <mat-label>Neighborhood / Area</mat-label>
                  <input matInput formControlName="neighborhood" placeholder="e.g., Midtown, Downtown, Times Square">
                  <mat-icon matSuffix>location_on</mat-icon>
                </mat-form-field>

                <mat-form-field appearance="outline">
                  <mat-label>Analysis Scenario</mat-label>
                  <mat-select formControlName="scenario">
                    <mat-option [value]="">-- Use Default (from settings) --</mat-option>
                    <mat-option value="surveillance">Surveillance</mat-option>
                    <mat-option value="traffic">Traffic</mat-option>
                    <mat-option value="nhl">NHL</mat-option>
                    <mat-option value="sports">Sports</mat-option>
                    <mat-option value="retail">Retail</mat-option>
                    <mat-option value="warehouse">Warehouse</mat-option>
                    <mat-option value="nyc_control">NYC Control</mat-option>
                    <mat-option value="egocentric">Egocentric (Kitchen/Barista/Sports/Finding)</mat-option>
                    <mat-option value="general">General</mat-option>
                  </mat-select>
                  <mat-icon matSuffix>psychology</mat-icon>
                </mat-form-field>
              </div>

              <button mat-raised-button class="action-btn" (click)="startCapture()" 
                      [disabled]="!startForm.valid || startLoading()">
                @if (startLoading()) {
                  <mat-spinner diameter="20"></mat-spinner>
                } @else {
                  <mat-icon>play_arrow</mat-icon>
                }
                <span>Trigger New Streaming Processing</span>
              </button>
            </form>

            @if (startResult()) {
              <div class="result-box" [class.success]="startResult()?.success" [class.error]="!startResult()?.success">
                <div class="result-header">
                  <mat-icon>{{ startResult()?.success ? 'check_circle' : 'error' }}</mat-icon>
                  <span>{{ startResult()?.success ? 'Success' : 'Error' }}</span>
                </div>
                <pre class="result-content">{{ formatJSON(startResult()) }}</pre>
              </div>
            }
          </div>
        </mat-tab>

        <!-- Tab 3: Stop Capture -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon>stop</mat-icon>
            <span>Stop Capture</span>
          </ng-template>
          <div class="tab-content">
            <p class="tab-description">Stop the currently running video capture process</p>
            
            <button mat-raised-button class="action-btn stop-btn" (click)="stopCapture()" [disabled]="stopLoading()">
              @if (stopLoading()) {
                <mat-spinner diameter="20"></mat-spinner>
              } @else {
                <mat-icon>stop</mat-icon>
              }
              <span>Stop Video Processing</span>
            </button>

            @if (stopResult()) {
              <div class="result-box" [class.success]="stopResult()?.success" [class.error]="!stopResult()?.success">
                <div class="result-header">
                  <mat-icon>{{ stopResult()?.success ? 'check_circle' : 'error' }}</mat-icon>
                  <span>{{ stopResult()?.success ? 'Stopped' : 'Error' }}</span>
                </div>
                <pre class="result-content">{{ formatJSON(stopResult()) }}</pre>
              </div>
            }
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .streaming-dialog {
      width: 600px;
      max-height: 80vh;
      background: var(--bg-card);
      color: var(--text-primary);
      display: flex;
      flex-direction: column;
      transition: background 0.3s ease, color 0.3s ease;
    }

    .dialog-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1.5rem 1.5rem 1rem 1.5rem;
      background: transparent;

      .header-icon {
        font-size: 28px;
        width: 28px;
        height: 28px;
        color: var(--accent-primary);
      }

      h2 {
        flex: 1;
        margin: 0;
        font-size: 1.25rem;
        font-weight: 500;
        color: var(--text-primary);
      }

      .close-btn {
        background: transparent !important;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        min-width: 40px !important;
        transition: all 0.2s ease;
        
        mat-icon {
          color: var(--text-secondary);
          font-size: 24px;
          width: 24px;
          height: 24px;
        }

        &:hover {
          background: var(--bg-card-hover) !important;
          
          mat-icon {
            color: var(--text-primary);
          }
        }
      }
    }

    ::ng-deep .streaming-tabs {
      flex: 1;
      display: flex;
      flex-direction: column;

      .mat-mdc-tab-header {
        background: rgba(0, 71, 171, 0.1);
        border-bottom: 1px solid rgba(0, 206, 209, 0.2);
      }

      .mat-mdc-tab-labels {
        justify-content: space-around;
      }

      .mat-mdc-tab-label {
        color: var(--text-primary) !important;
        opacity: 1 !important;

        mat-icon {
          margin-right: 0.5rem;
          color: var(--text-primary) !important;
        }

        &.mdc-tab--active {
          color: var(--accent-primary) !important;
          
          mat-icon {
            color: var(--accent-primary) !important;
          }
        }
        
        .mdc-tab__text-label, .mat-mdc-tab-label-content, span {
          color: var(--text-primary) !important;
        }
        
        &.mdc-tab--active .mdc-tab__text-label,
        &.mdc-tab--active .mat-mdc-tab-label-content,
        &.mdc-tab--active span {
          color: var(--accent-primary) !important;
        }
      }
      
      .mat-mdc-tab .mdc-tab__text-label {
        color: var(--text-primary) !important;
      }
      
      .mat-mdc-tab.mdc-tab--active .mdc-tab__text-label {
        color: var(--accent-primary) !important;
      }

      .mat-mdc-tab-body-wrapper {
        flex: 1;
      }
    }

    .tab-content {
      padding: 1.5rem;
      overflow-y: auto;
      max-height: 500px;
    }

    .tab-description {
      color: var(--text-secondary);
      margin-bottom: 1.5rem;
      font-size: 0.95rem;
    }

    .streaming-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;

      ::ng-deep .mat-mdc-form-field {
        .mat-mdc-text-field-wrapper {
          background: var(--bg-secondary);
        }

        .mat-mdc-form-field-flex {
          background: var(--bg-secondary);
        }

        input {
          color: var(--text-primary) !important;
          caret-color: var(--accent-primary) !important;
        }

        input::placeholder {
          color: var(--text-muted) !important;
        }

        .mat-mdc-form-field-label {
          color: var(--text-secondary) !important;
        }

        .mat-mdc-floating-label {
          color: var(--text-secondary) !important;
        }

        .mat-icon {
          color: var(--accent-primary) !important;
        }

        .mdc-text-field--filled {
          background-color: var(--bg-secondary) !important;
        }

        .mat-mdc-input-element {
          color: var(--text-primary) !important;
        }

        .mat-mdc-select-value {
          color: var(--text-primary) !important;
        }

        .mat-mdc-select-arrow {
          color: var(--text-secondary) !important;
        }
      }
    }

    .metadata-section {
      margin-top: 1.5rem;
      padding: 1.25rem;
      background: rgba(0, 71, 171, 0.08);
      border: 1px solid rgba(0, 206, 209, 0.2);
      border-radius: 8px;

      .section-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0 0 0.5rem 0;
        color: #00CED1;
        font-size: 1rem;
        font-weight: 500;

        mat-icon {
          font-size: 20px;
          width: 20px;
          height: 20px;
          color: #00CED1;
        }
      }

      .section-description {
        margin: 0 0 1rem 0;
        color: var(--text-secondary);
        font-size: 0.875rem;
        line-height: 1.5;
      }

      ::ng-deep .mat-mdc-form-field {
        margin-bottom: 0.5rem;
      }
    }

    .action-btn {
      background: var(--button-bg-primary) !important;
      color: var(--button-text) !important;
      border: 1px solid var(--border-color) !important;
      padding: 0.75rem 1.5rem !important;
      font-size: 1rem !important;
      display: flex !important;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      margin-top: 1rem;
      cursor: pointer !important;
      user-select: none !important;
      -webkit-user-select: none !important;
      -moz-user-select: none !important;
      -ms-user-select: none !important;
      transition: all 0.3s ease;

      * {
        color: var(--button-text) !important;
      }

      mat-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      mat-spinner {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
      }
      
      ::ng-deep .mat-mdc-progress-spinner {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
      }

      span {
        user-select: none !important;
        cursor: pointer !important;
      }

      &:hover:not([disabled]) {
        background: var(--button-bg-hover) !important;
        border-color: var(--border-hover) !important;
      }

      &[disabled] {
        opacity: 0.5;
        cursor: not-allowed !important;
        
        * {
          cursor: not-allowed !important;
        }
      }
      
      * {
        cursor: pointer !important;
        user-select: none !important;
      }
    }

    .stop-btn {
      background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
      border-color: rgba(239, 68, 68, 0.4) !important;

      &:hover:not([disabled]) {
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
        border-color: rgba(239, 68, 68, 0.6) !important;
      }
    }

    .result-box {
      margin-top: 1.5rem;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid;

      &.success {
        border-color: rgba(6, 255, 165, 0.4);
        background: rgba(6, 255, 165, 0.05);
      }

      &.error {
        border-color: rgba(239, 68, 68, 0.4);
        background: rgba(239, 68, 68, 0.05);
      }

      .result-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
        background: rgba(0, 0, 0, 0.2);
        font-weight: 600;

        mat-icon {
          font-size: 20px;
          width: 20px;
          height: 20px;
        }
      }

      &.success .result-header {
        color: #06ffa5;
        mat-icon {
          color: #06ffa5;
        }
      }

      &.error .result-header {
        color: #ef4444;
        mat-icon {
          color: #ef4444;
        }
      }

      .result-content {
        padding: 1rem;
        margin: 0;
        font-family: 'Roboto Mono', monospace;
        font-size: 0.85rem;
        color: var(--text-primary);
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-x: auto;
      }
    }

    ::ng-deep .mat-mdc-progress-spinner {
      --mdc-circular-progress-active-indicator-color: #00CED1;
    }

    // Style the mat-select dropdown panel to match the dark theme
    ::ng-deep .mat-mdc-select-panel {
      background: linear-gradient(135deg, #0A0A1E 0%, #15152E 100%) !important;
      border: 1px solid rgba(0, 206, 209, 0.3) !important;
      border-radius: 8px !important;

      .mat-mdc-option {
        color: var(--text-primary) !important;
        background: transparent !important;

        &:hover:not(.mdc-list-item--disabled) {
          background: var(--bg-card-hover) !important;
        }

        &.mdc-list-item--selected:not(.mdc-list-item--disabled) {
          background: var(--bg-card) !important;
          color: var(--accent-primary) !important;
        }

        .mdc-list-item__primary-text {
          color: inherit !important;
        }
      }
    }
  `]
})
export class StreamingConfigComponent {
  private dialogRef = inject(MatDialogRef<StreamingConfigComponent>);
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private streamingService = inject(StreamingService);

  statusLoading = signal(false);
  statusResult = signal<any>(null);

  startLoading = signal(false);
  startResult = signal<any>(null);

  stopLoading = signal(false);
  stopResult = signal<any>(null);

  startForm: FormGroup;

  constructor() {
    // Initialize form first
    this.startForm = this.fb.group({
      youtube_url: ['', [Validators.required]],
      access_key: ['', [Validators.required]],
      secret_key: ['', [Validators.required]],
      s3_endpoint: ['', [Validators.required]],
      bucket_name: ['', [Validators.required]],
      name: ['capture', [Validators.required]],
      capture_interval: [10, [Validators.required, Validators.min(1), Validators.max(300)]],
      // Stream capture metadata (optional)
      camera_id: [''],
      capture_type: [''],
      neighborhood: [''],
      scenario: ['']
    });

    // Load streaming prefill config from backend (includes actual credentials)
    this.streamingService.getPrefillConfig().subscribe({
      next: (config) => {
        this.startForm.patchValue({
          s3_endpoint: config.s3_endpoint || '',
          bucket_name: config.bucket_name || '',
          access_key: config.s3_access_key || '',
          secret_key: config.s3_secret_key || ''
        });
        console.log('[STREAMING] Pre-filled S3 config from backend');
      },
      error: (err: any) => {
        console.error('Failed to load streaming prefill config:', err);
        // Fallback to config endpoint for non-sensitive data
        this.http.get<any>(`${environment.apiUrl}/config`).subscribe({
          next: (config: any) => {
            this.startForm.patchValue({
              s3_endpoint: config.s3?.s3_endpoint || '',
              bucket_name: config.s3?.s3_upload_bucket || ''
            });
          },
          error: (fallbackErr: any) => {
            console.error('Fallback config load also failed:', fallbackErr);
          }
        });
      }
    });
  }

  checkStatus() {
    this.statusLoading.set(true);
    this.statusResult.set(null);

    this.streamingService.getStatus().subscribe({
      next: (data: any) => {
        this.statusResult.set(data);
        this.statusLoading.set(false);
      },
      error: (err: any) => {
        this.statusResult.set({
          success: false,
          error: err.error?.detail || err.message || 'Failed to get status'
        });
        this.statusLoading.set(false);
      }
    });
  }

  startCapture() {
    if (!this.startForm.valid) return;

    this.startLoading.set(true);
    this.startResult.set(null);

    const request: StreamingStartRequest = this.startForm.value;

    this.streamingService.start(request).subscribe({
      next: (data: any) => {
        this.startResult.set(data);
        this.startLoading.set(false);
      },
      error: (err: any) => {
        this.startResult.set({
          success: false,
          error: err.error?.detail || err.message || 'Failed to start capture'
        });
        this.startLoading.set(false);
      }
    });
  }

  stopCapture() {
    this.stopLoading.set(true);
    this.stopResult.set(null);

    this.streamingService.stop().subscribe({
      next: (data: any) => {
        this.stopResult.set(data);
        this.stopLoading.set(false);
      },
      error: (err: any) => {
        this.stopResult.set({
          success: false,
          error: err.error?.detail || err.message || 'Failed to stop capture'
        });
        this.stopLoading.set(false);
      }
    });
  }

  formatJSON(obj: any): string {
    return JSON.stringify(obj, null, 2);
  }

  close() {
    this.dialogRef.close();
  }
}

