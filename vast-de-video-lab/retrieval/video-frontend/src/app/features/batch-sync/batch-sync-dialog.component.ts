import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators, FormGroup } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSliderModule } from '@angular/material/slider';
import { BatchSyncService, BatchSyncStartRequest, BatchSyncCheckObjectsRequest } from '../../shared/services/batch-sync.service';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-batch-sync-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatCheckboxModule,
    MatProgressSpinnerModule,
    MatSliderModule
  ],
  template: `
    <div class="batch-sync-dialog">
      <div class="dialog-header">
        <mat-icon class="header-icon">sync</mat-icon>
        <h2>S3 Batch Video Sync</h2>
        <button mat-icon-button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-content">
        <p class="description">
          Copy MP4 files from a source S3 bucket to the destination bucket using server-side copy operations.
          Files are automatically processed by the ingest pipeline after copying.
        </p>

        <form [formGroup]="syncForm" class="sync-form">
          <!-- Use Default Checkbox -->
          <label class="checkbox-wrapper">
            <input type="checkbox" formControlName="useDefault" class="custom-checkbox" (change)="onUseDefaultChange()">
            <span class="checkbox-label">
              <mat-icon class="checkbox-icon">{{ syncForm.get('useDefault')?.value ? 'check_box' : 'check_box_outline_blank' }}</mat-icon>
              Use default S3 credentials (from backend config)
            </span>
          </label>

          <!-- Source S3 Configuration -->
          <h3 class="section-title">
            <mat-icon>cloud_upload</mat-icon>
            <span>Source S3 Configuration</span>
          </h3>

          <mat-form-field appearance="outline">
            <mat-label>S3 Endpoint</mat-label>
            <input matInput formControlName="source_s3_endpoint" placeholder="http://your-s3-endpoint">
            <mat-icon matSuffix>cloud</mat-icon>
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>S3 Access Key</mat-label>
            <input matInput formControlName="source_access_key" placeholder="Enter S3 access key">
            <mat-icon matSuffix>vpn_key</mat-icon>
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>S3 Secret Key</mat-label>
            <input matInput 
                   type="password" 
                   formControlName="source_secret_key" 
                   placeholder="Enter S3 secret key"
                   [readonly]="syncForm.get('useDefault')?.value">
            <mat-icon matSuffix>lock</mat-icon>
          </mat-form-field>

          <div class="bucket-path-row">
            <mat-form-field appearance="outline" class="bucket-path-field">
              <mat-label>Bucket / Path</mat-label>
              <input matInput formControlName="source_bucket_path" placeholder="bucket-name or bucket-name/path/to/videos/">
              <mat-icon matSuffix>folder</mat-icon>
            </mat-form-field>

            <button mat-raised-button type="button" class="check-btn" 
                    (click)="checkObjects()" 
                    [disabled]="checkingObjects() || !canCheckObjects()">
              @if (checkingObjects()) {
                <mat-spinner diameter="20"></mat-spinner>
              } @else {
                <mat-icon>search</mat-icon>
              }
              <span>Check Videos</span>
            </button>
          </div>

          @if (checkResult()) {
            <div class="check-result" [class.success]="checkResult()?.success" [class.error]="!checkResult()?.success">
              <mat-icon>{{ checkResult()?.success ? 'check_circle' : 'error' }}</mat-icon>
              <span>
                @if (checkResult()?.success) {
                  Found {{ checkResult()?.count }} MP4 file(s)
                } @else {
                  {{ checkResult()?.error || 'Failed to check objects' }}
                }
              </span>
            </div>
          }

          <!-- Destination S3 Information -->
          <div class="destination-info">
            <mat-icon>cloud_download</mat-icon>
            <div class="destination-text">
              <span class="destination-label">Destination:</span>
              <span class="destination-value">s3://{{ getDestinationBucket() }}</span>
            </div>
          </div>

          <!-- Batch Configuration -->
          <h3 class="section-title">
            <mat-icon>settings</mat-icon>
            <span>Batch Configuration</span>
          </h3>

          <div class="slider-container">
            <div class="slider-labels">
              <span class="slider-label">Fast (0.1s)</span>
              <span class="slider-value">{{ syncForm.get('batch_size')?.value || 1 }}s</span>
              <span class="slider-label">Slow (60s)</span>
            </div>
            <mat-slider min="0.1" max="60" step="0.1" class="delay-slider">
              <input matSliderThumb formControlName="batch_size">
            </mat-slider>
          </div>

          <!-- Video Metadata -->
          <h3 class="section-title">
            <mat-icon>info</mat-icon>
            <span>Video Metadata (Applied to All Files)</span>
          </h3>

          <mat-form-field appearance="outline">
            <mat-label>Tags</mat-label>
            <input matInput formControlName="tags" placeholder="demo, outdoor, test">
            <mat-icon matSuffix>label</mat-icon>
            <span class="field-hint">Comma-separated tags</span>
          </mat-form-field>

          <label class="checkbox-wrapper">
            <input type="checkbox" formControlName="isPrivate" class="custom-checkbox">
            <span class="checkbox-label">
              <mat-icon class="checkbox-icon">{{ syncForm.get('isPrivate')?.value ? 'check_box' : 'check_box_outline_blank' }}</mat-icon>
              Make videos private (visible to allowed users only)
            </span>
          </label>

          @if (syncForm.get('isPrivate')?.value) {
            <mat-form-field appearance="outline">
              <mat-label>Allowed Users</mat-label>
              <input matInput formControlName="allowedUsers" placeholder="john.doe, jane.smith">
              <mat-icon matSuffix>people</mat-icon>
              <span class="field-hint">Comma-separated list of allowed users</span>
            </mat-form-field>
          }

          <!-- Streaming Metadata (Optional) -->
          <h3 class="section-title">
            <mat-icon>videocam</mat-icon>
            <span>Stream Metadata (Optional)</span>
          </h3>

          <mat-form-field appearance="outline">
            <mat-label>Camera ID</mat-label>
            <input matInput formControlName="camera_id" placeholder="e.g., CAM-001, manhattan-cam-1">
            <mat-icon matSuffix>videocam</mat-icon>
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>Capture Type</mat-label>
            <input matInput formControlName="capture_type" placeholder="traffic, streets, crowds, malls">
            <mat-icon matSuffix>category</mat-icon>
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>Neighborhood / Area</mat-label>
            <input matInput formControlName="neighborhood" placeholder="e.g., Midtown, Downtown">
            <mat-icon matSuffix>location_on</mat-icon>
          </mat-form-field>

          @if (error()) {
            <div class="error-message">
              <mat-icon>error_outline</mat-icon>
              <span>{{ error() }}</span>
            </div>
          }

          <div class="dialog-actions">
            <button mat-button class="cancel-btn" (click)="close()">Cancel</button>
            <button mat-raised-button class="start-btn" 
                    (click)="startSync()" 
                    [disabled]="!syncForm.valid || starting() || !checkResult()?.success">
              @if (starting()) {
                <mat-spinner diameter="20"></mat-spinner>
              } @else {
                <mat-icon>play_arrow</mat-icon>
              }
              <span>Start Batch Sync</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .batch-sync-dialog {
      width: 700px;
      max-height: 90vh;
      background: linear-gradient(135deg, #0A0A1E 0%, #15152E 100%);
      color: white;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border-radius: 12px;
      
      // Ensure buttons are clickable
      button {
        cursor: pointer !important;
        
        &[disabled] {
          cursor: not-allowed !important;
        }
        
        * {
          cursor: pointer !important;
        }
        
        &[disabled] * {
          cursor: not-allowed !important;
        }
      }
    }

    .dialog-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1.5rem 1.5rem 1rem 1.5rem;
      background: transparent;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      margin: 0;
      border-top-left-radius: 12px;
      border-top-right-radius: 12px;

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
        background: transparent !important;
        border: none;
        cursor: pointer;
        color: rgba(255, 255, 255, 0.7);
        &:hover {
          color: white;
          background: rgba(255, 255, 255, 0.1) !important;
        }
      }
    }

    .dialog-content {
      padding: 1.5rem;
      overflow-y: auto;
      flex: 1;
    }

    .description {
      color: rgba(255, 255, 255, 0.7);
      margin-bottom: 1.5rem;
      font-size: 0.95rem;
      line-height: 1.5;
    }

    .sync-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .section-title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin: 1.5rem 0 0.75rem 0;
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

    .bucket-path-row {
      display: flex;
      gap: 1rem;
      align-items: flex-start;

      .bucket-path-field {
        flex: 1;
      }

      .check-btn {
        background: linear-gradient(135deg, #0047AB 0%, #002766 100%) !important;
        color: white !important;
        white-space: nowrap;
        height: 48px;
        min-width: 140px;
        margin-top: 0;
        align-self: flex-start;
        cursor: pointer !important;
        
        &:hover:not([disabled]) {
          background: linear-gradient(135deg, #0056D6 0%, #0047AB 100%) !important;
          box-shadow: 0 4px 12px rgba(0, 71, 171, 0.4);
        }
        
        &[disabled] {
          cursor: not-allowed !important;
          opacity: 0.5;
        }
        
        * {
          cursor: pointer !important;
        }
        
        &[disabled] * {
          cursor: not-allowed !important;
        }
      }
    }

    .checkbox-wrapper {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin: 0.5rem 0 1.5rem 0;
      cursor: pointer;
      padding: 0.75rem 1rem;
      background: rgba(0, 71, 171, 0.08);
      border: 1px solid rgba(0, 71, 171, 0.25);
      border-radius: 12px;
      transition: all 0.3s ease;
      
      &:hover {
        background: rgba(0, 71, 171, 0.15);
        border-color: rgba(0, 71, 171, 0.4);
      }
      
      .custom-checkbox {
        position: absolute;
        opacity: 0;
        cursor: pointer;
      }
      
      .checkbox-label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.95rem;
        cursor: pointer;
        
        .checkbox-icon {
          color: #00d9ff;
          font-size: 1.5rem;
          width: 1.5rem;
          height: 1.5rem;
        }
      }
    }

    .check-result {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      margin-top: 0.5rem;

      &.success {
        background: rgba(6, 255, 165, 0.1);
        border: 1px solid rgba(6, 255, 165, 0.3);
        color: #06ffa5;

        mat-icon {
          color: #06ffa5;
        }
      }

      &.error {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #ef4444;

        mat-icon {
          color: #ef4444;
        }
      }
    }

    .destination-info {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      margin-top: 0.5rem;
      background: rgba(0, 206, 209, 0.1);
      border: 1px solid rgba(0, 206, 209, 0.3);
      border-radius: 8px;
      color: rgba(255, 255, 255, 0.9);

      mat-icon {
        color: #00CED1;
        font-size: 20px;
        width: 20px;
        height: 20px;
      }

      .destination-text {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;

        .destination-label {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.6);
        }

        .destination-value {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.9rem;
          font-weight: 600;
          color: #00CED1;
        }
      }
    }

    .error-message {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      background: rgba(220, 38, 38, 0.12);
      border: 1px solid rgba(220, 38, 38, 0.4);
      border-radius: 12px;
      padding: 1rem;
      color: rgba(252, 165, 165, 0.95);
      margin-top: 1rem;

      mat-icon {
        color: #f87171;
      }
    }

    .field-hint {
      display: block;
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.5);
      margin-top: 0.25rem;
      margin-bottom: 0.5rem;
      font-style: italic;
    }

    .slider-container {
      width: 100%;
      padding: 0.5rem 0.5rem 1rem 0.5rem;
    }

    .slider-labels {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
      
      .slider-label {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.5);
      }
      
      .slider-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        font-weight: 600;
        color: #00CED1;
        background: rgba(0, 206, 209, 0.1);
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
      }
    }

    .delay-slider {
      width: 100%;
      
      ::ng-deep {
        .mdc-slider__track--inactive {
          background: rgba(255, 255, 255, 0.2) !important;
        }
        
        .mdc-slider__track--active_fill {
          background: linear-gradient(90deg, #00CED1, #0047AB) !important;
          border-color: transparent !important;
        }
        
        .mdc-slider__thumb-knob {
          background: #00CED1 !important;
          border-color: #00CED1 !important;
          box-shadow: 0 0 10px rgba(0, 206, 209, 0.5);
          cursor: pointer !important;
        }
        
        .mdc-slider__thumb {
          cursor: pointer !important;
        }
      }
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
      margin-top: 1.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);

      .cancel-btn {
        color: rgba(255, 255, 255, 0.7);
        cursor: pointer !important;
        
        &:hover {
          background: rgba(255, 255, 255, 0.1);
        }
        
        * {
          cursor: pointer !important;
        }
      }

      .start-btn {
        background: linear-gradient(135deg, #0047AB 0%, #002766 100%) !important;
        color: white !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer !important;
        
        &:hover:not([disabled]) {
          background: linear-gradient(135deg, #0056D6 0%, #0047AB 100%) !important;
          box-shadow: 0 4px 12px rgba(0, 71, 171, 0.4);
        }
        
        &[disabled] {
          cursor: not-allowed !important;
          opacity: 0.5;
        }
        
        * {
          cursor: pointer !important;
        }
        
        &[disabled] * {
          cursor: not-allowed !important;
        }
      }
    }

    ::ng-deep .mat-mdc-form-field {
      .mat-mdc-text-field-wrapper {
        background: rgba(0, 71, 171, 0.1);
      }

      .mat-mdc-form-field-flex {
        background: rgba(0, 71, 171, 0.1);
      }

      input {
        color: #00CED1 !important;
        caret-color: #00CED1 !important;
      }

      input::placeholder {
        color: rgba(0, 206, 209, 0.5) !important;
      }

      .mat-mdc-form-field-label {
        color: rgba(0, 206, 209, 0.7) !important;
      }

      .mat-icon {
        color: #00CED1 !important;
      }

      .mdc-notched-outline__leading,
      .mdc-notched-outline__notch,
      .mdc-notched-outline__trailing {
        border-color: rgba(255, 255, 255, 0.2) !important;
      }
    }
  `]
})
export class BatchSyncDialogComponent implements OnInit {
  private dialogRef = inject(MatDialogRef<BatchSyncDialogComponent>);
  private fb = inject(FormBuilder);
  private batchSyncService = inject(BatchSyncService);
  private http = inject(HttpClient);

  syncForm: FormGroup;
  checkingObjects = signal(false);
  checkResult = signal<any>(null);
  starting = signal(false);
  error = signal<string | null>(null);
  defaultConfig: any = null;

  constructor() {
    this.syncForm = this.fb.group({
      useDefault: [false],
      // Source S3
      source_s3_endpoint: ['', [Validators.required]],
      source_access_key: ['', [Validators.required]],
      source_secret_key: ['', [Validators.required]],
      source_bucket_path: ['', [Validators.required]],
      // Batch config
      batch_size: [1, [Validators.required, Validators.min(0.1), Validators.max(60)]],
      // Metadata
      tags: [''],
      isPrivate: [false],
      allowedUsers: [''],
      // Streaming metadata
      camera_id: [''],
      capture_type: [''],
      neighborhood: ['']
    });
  }

  ngOnInit() {
    // Reset form state to prevent stale data
    this.error.set(null);
    this.checkResult.set(null);
    this.checkingObjects.set(false);
    this.starting.set(false);
    
    // Load prefill config
    this.batchSyncService.getPrefillConfig().subscribe({
      next: (config: any) => {
        // Store for use when "use default" is checked
        this.defaultConfig = config;
        (this as any).defaultConfig = config;
      },
      error: (err: any) => {
        console.error('Failed to load batch sync prefill config:', err);
      }
    });
  }

  getDestinationBucket(): string {
    return this.defaultConfig?.bucket_name || 'default-bucket';
  }

  onUseDefaultChange() {
    const useDefault = this.syncForm.get('useDefault')?.value;
    const defaultConfig = (this as any).defaultConfig;

    if (useDefault && defaultConfig) {
      // Mask secret key (show only first 4 and last 4 characters)
      const secretKey = defaultConfig.s3_secret_key || '';
      const maskedSecret = secretKey.length > 8 
        ? secretKey.substring(0, 4) + '•'.repeat(secretKey.length - 8) + secretKey.substring(secretKey.length - 4)
        : '•'.repeat(secretKey.length || 8);
      
      this.syncForm.patchValue({
        source_s3_endpoint: defaultConfig.s3_endpoint || '',
        source_access_key: defaultConfig.s3_access_key || '',
        source_secret_key: maskedSecret
        // Note: source_bucket is NOT prefilled - user must specify it manually
      });
      
      // Store actual secret for when form is submitted
      (this as any).actualSecretKey = secretKey;
    } else {
      // Clear the form when unchecked
      this.syncForm.patchValue({
        source_secret_key: ''
      });
      (this as any).actualSecretKey = null;
    }
  }

  canCheckObjects(): boolean {
    // Check if we have actual secret key (either from form or from default config)
    const actualSecretKey = (this as any).actualSecretKey;
    const hasSecretKey = actualSecretKey || this.syncForm.get('source_secret_key')?.value;
    
    return !!(
      this.syncForm.get('source_s3_endpoint')?.value &&
      this.syncForm.get('source_access_key')?.value &&
      hasSecretKey &&
      this.syncForm.get('source_bucket_path')?.value
    );
  }

  private parseBucketPath(bucketPath: string): { bucket: string; prefix: string } {
    // Parse "bucket" or "bucket/prefix" format
    const trimmed = bucketPath.trim();
    if (!trimmed) {
      return { bucket: '', prefix: '' };
    }
    
    // Split on first '/' to separate bucket from prefix
    const parts = trimmed.split('/', 2);
    const bucket = parts[0];
    const prefix = parts.length > 1 ? parts[1] : '';
    
    return { bucket, prefix };
  }

  checkObjects() {
    if (!this.canCheckObjects()) return;

    this.checkingObjects.set(true);
    this.checkResult.set(null);
    this.error.set(null);

    const formValue = this.syncForm.value;
    
    // Use actual secret key if "use default" was checked
    const actualSecretKey = (this as any).actualSecretKey;
    const sourceSecretKey = actualSecretKey || formValue.source_secret_key;
    
    const { bucket, prefix } = this.parseBucketPath(formValue.source_bucket_path);
    
    const request: BatchSyncCheckObjectsRequest = {
      access_key: formValue.source_access_key,
      secret_key: sourceSecretKey,
      s3_endpoint: formValue.source_s3_endpoint,
      bucket: bucket,
      prefix: prefix,
      use_ssl: formValue.source_s3_endpoint?.startsWith('https://')
    };

    this.batchSyncService.checkObjects(request).subscribe({
      next: (result: any) => {
        this.checkResult.set(result);
        this.checkingObjects.set(false);
      },
      error: (err: any) => {
        let errorMessage = 'Failed to check objects';
        
        // Handle different error formats
        if (err.error) {
          if (typeof err.error === 'string') {
            errorMessage = err.error;
          } else if (err.error.detail) {
            errorMessage = typeof err.error.detail === 'string' ? err.error.detail : JSON.stringify(err.error.detail);
          } else if (err.error.error) {
            errorMessage = typeof err.error.error === 'string' ? err.error.error : JSON.stringify(err.error.error);
          } else if (err.error.message) {
            errorMessage = typeof err.error.message === 'string' ? err.error.message : JSON.stringify(err.error.message);
          } else if (typeof err.error === 'object') {
            // Try to extract meaningful error from object
            const errorStr = JSON.stringify(err.error);
            if (errorStr !== '{}') {
              errorMessage = errorStr;
            }
          }
        } else if (err.message) {
          errorMessage = err.message;
        }
        
        this.checkResult.set({
          success: false,
          error: errorMessage,
          count: 0
        });
        this.checkingObjects.set(false);
      }
    });
  }

  startSync() {
    if (!this.syncForm.valid || !this.checkResult()?.success) {
      if (!this.syncForm.valid) {
        this.error.set('Please fill in all required fields correctly');
      } else if (!this.checkResult()?.success) {
        this.error.set('Please check videos first to ensure files are available');
      }
      return;
    }

    this.starting.set(true);
    this.error.set(null);
    
    // Clear any previous check result to prevent stale state
    // The check result is only needed for validation, not for submission

    const formValue = this.syncForm.value;

    // Use actual secret key if "use default" was checked
    const actualSecretKey = (this as any).actualSecretKey;
    const sourceSecretKey = actualSecretKey || formValue.source_secret_key;

    // Parse tags and allowed users
    const tags = formValue.tags
      ? formValue.tags.split(',').map((t: string) => t.trim()).filter((t: string) => t)
      : [];

    const allowedUsers = formValue.allowedUsers
      ? formValue.allowedUsers.split(',').map((u: string) => u.trim()).filter((u: string) => u)
      : [];

    const { bucket, prefix } = this.parseBucketPath(formValue.source_bucket_path);
    
    const request: BatchSyncStartRequest = {
      source_access_key: formValue.source_access_key,
      source_secret_key: sourceSecretKey,
      source_s3_endpoint: formValue.source_s3_endpoint,
      source_bucket: bucket,
      source_prefix: prefix,
      source_use_ssl: formValue.source_s3_endpoint?.startsWith('https://'),
      batch_size: formValue.batch_size,
      is_public: !formValue.isPrivate,
      tags: tags.length > 0 ? tags : undefined,
      allowed_users: allowedUsers.length > 0 ? allowedUsers : undefined,
      camera_id: formValue.camera_id || undefined,
      capture_type: formValue.capture_type || undefined,
      neighborhood: formValue.neighborhood || undefined
    };

    this.batchSyncService.start(request).subscribe({
      next: (result: any) => {
        this.starting.set(false);
        if (result.success) {
          this.dialogRef.close({ started: true, job_id: result.job_id });
        } else {
          // Handle error response from backend
          const errorMsg = result.error || result.message || 'Failed to start batch sync';
          this.error.set(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
        }
      },
      error: (err: any) => {
        let errorMessage = 'Failed to start batch sync';
        
        // Handle different error formats
        if (err.error) {
          if (typeof err.error === 'string') {
            errorMessage = err.error;
          } else if (err.error.detail) {
            errorMessage = typeof err.error.detail === 'string' ? err.error.detail : JSON.stringify(err.error.detail);
          } else if (err.error.error) {
            errorMessage = typeof err.error.error === 'string' ? err.error.error : JSON.stringify(err.error.error);
          } else if (err.error.message) {
            errorMessage = typeof err.error.message === 'string' ? err.error.message : JSON.stringify(err.error.message);
          } else if (typeof err.error === 'object') {
            // Try to extract meaningful error from object
            const errorStr = JSON.stringify(err.error);
            if (errorStr !== '{}') {
              errorMessage = errorStr;
            }
          }
        } else if (err.message) {
          errorMessage = err.message;
        }
        
        this.error.set(errorMessage);
        this.starting.set(false);
      }
    });
  }

  close() {
    this.dialogRef.close();
  }
}

