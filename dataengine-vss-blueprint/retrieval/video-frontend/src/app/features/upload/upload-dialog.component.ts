import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { VideoService } from '../../shared/services/video.service';
import { UploadRequest } from '../../shared/models/video.model';

@Component({
  selector: 'app-upload-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule
  ],
  template: `
    <div class="upload-dialog-container">
      <h2 mat-dialog-title>
        <mat-icon>cloud_upload</mat-icon>
        Upload Video
      </h2>

      <mat-dialog-content>
        @if (!uploading() && !uploadComplete()) {
          <form [formGroup]="uploadForm">
            <div class="drop-zone" 
                 [class.drag-over]="isDragOver()"
                 (dragover)="onDragOver($event)"
                 (dragleave)="onDragLeave($event)"
                 (drop)="onDrop($event)"
                 (click)="fileInput.click()">
              <mat-icon class="upload-icon">video_file</mat-icon>
              <p class="drop-text">
                @if (!selectedFile()) {
                  Drag & drop video file here or click to browse
                } @else {
                  {{ selectedFile()?.name }}
                }
              </p>
              <p class="drop-hint">Max file size: 25MB • Supported: MP4 only (required by NVIDIA Cosmos)</p>
              <input #fileInput type="file" hidden accept="video/mp4,.mp4" (change)="onFileSelected($event)">
            </div>

            <div class="form-field-wrapper">
              <label class="field-label">Tags</label>
              <input type="text" 
                     class="custom-input" 
                     formControlName="tags" 
                     placeholder="demo, outdoor, test">
              <span class="field-hint">Add comma-separated tags to categorize your video</span>
            </div>

            <div class="form-field-wrapper">
              <label class="field-label">Analysis Scenario</label>
              <select class="custom-input" formControlName="scenario">
                <option value="">-- Use Default (from settings) --</option>
                <option value="surveillance">Surveillance</option>
                <option value="traffic">Traffic</option>
                <option value="nhl">NHL</option>
                <option value="sports">Sports</option>
                <option value="retail">Retail</option>
                <option value="warehouse">Warehouse</option>
                <option value="nyc_control">NYC Control</option>
                <option value="egocentric">Egocentric (Kitchen/Barista/Sports/Finding)</option>
                <option value="general">General</option>
              </select>
              <span class="field-hint">Select the analysis prompt scenario for this video</span>
            </div>

            <label class="checkbox-wrapper">
              <input type="checkbox" formControlName="isPrivate" class="custom-checkbox">
              <span class="checkbox-label">
                <mat-icon class="checkbox-icon">{{ uploadForm.get('isPrivate')?.value ? 'check_box' : 'check_box_outline_blank' }}</mat-icon>
                Make this video private (visible to allowed users only)
              </span>
            </label>

            @if (uploadForm.get('isPrivate')?.value) {
              <div class="form-field-wrapper">
                <label class="field-label">Allowed Users</label>
                <input type="text" 
                       class="custom-input" 
                       formControlName="allowedUsers" 
                       placeholder="john.doe, jane.smith">
                <span class="field-hint">Specify users who can access this video (you are always included)</span>
              </div>
            }

            @if (error()) {
              <div class="error-message">
                <mat-icon>error_outline</mat-icon>
                <span>{{ error() }}</span>
              </div>
            }
          </form>
        }

        @if (uploading()) {
          <div class="upload-progress">
            <mat-icon class="progress-icon">{{ uploadPhase() === 'requesting' ? 'hourglass_empty' : 'cloud_upload' }}</mat-icon>
            <h3>{{ uploadPhaseText() }}</h3>
            <mat-progress-bar mode="indeterminate" color="primary"></mat-progress-bar>
            <p class="progress-detail">{{ uploadPhaseDetail() }}</p>
          </div>
        }

        @if (uploadComplete()) {
          <div class="upload-complete">
            <mat-icon class="success-icon">check_circle</mat-icon>
            <h3>Upload Successful!</h3>
            <p>Your video has been uploaded and is being processed by the AI pipeline.</p>
            <div class="processing-info">
              <div class="info-item">
                <mat-icon>movie_filter</mat-icon>
                <span>Segmenting video...</span>
              </div>
              <div class="info-item">
                <mat-icon>psychology</mat-icon>
                <span>Analyzing with Cosmos AI...</span>
              </div>
              <div class="info-item">
                <mat-icon>analytics</mat-icon>
                <span>Generating embeddings...</span>
              </div>
              <div class="info-item">
                <mat-icon>storage</mat-icon>
                <span>Storing in VastDB...</span>
              </div>
            </div>
            <p class="wait-message">Processing takes about 30-60 seconds per video. Your video will be searchable once complete.</p>
          </div>
        }
      </mat-dialog-content>

      <mat-dialog-actions>
        @if (!uploading() && !uploadComplete()) {
          <button mat-raised-button (click)="close()" class="cancel-button">Cancel</button>
          <button mat-raised-button color="primary" 
                  [disabled]="!canUpload()"
                  (click)="upload()">
            <mat-icon>upload</mat-icon>
            Upload
          </button>
        }
        @if (uploadComplete()) {
          <button mat-raised-button color="primary" (click)="close()">
            <mat-icon>done</mat-icon>
            Done
          </button>
        }
      </mat-dialog-actions>
    </div>
  `,
  styles: [`
    ::ng-deep .mat-mdc-dialog-surface {
      background: linear-gradient(135deg, rgba(10, 20, 40, 0.98) 0%, rgba(0, 10, 30, 0.98) 100%) !important;
      backdrop-filter: blur(20px);
      border: 1px solid rgba(0, 71, 171, 0.3);
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6) !important;
    }

    ::ng-deep .mat-mdc-dialog-container .mdc-dialog__surface {
      background: transparent !important;
    }

    .upload-dialog-container {
      ::ng-deep h2 {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: var(--text-primary);
        font-weight: 500;
        margin: 0 0 1rem 0 !important;
        padding: 0 !important;
        transition: color 0.3s ease;
        
        mat-icon {
          color: var(--accent-primary);
        }
      }
    }

    ::ng-deep mat-dialog-content {
      min-height: 300px;
      padding: 0 1.5rem 1.5rem 1.5rem !important;
    }
    
    ::ng-deep .mat-mdc-dialog-title {
      padding: 1.5rem 1.5rem 0 1.5rem !important;
    }

    .drop-zone {
      border: 2px dashed rgba(0, 71, 171, 0.4);
      border-radius: 16px;
      padding: 3rem 2rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      background: rgba(0, 71, 171, 0.08);
      margin-bottom: 1.5rem;
      
      &:hover {
        border-color: rgba(0, 71, 171, 0.7);
        background: rgba(0, 71, 171, 0.15);
      }
      
      &.drag-over {
        border-color: #00d9ff;
        background: rgba(0, 217, 255, 0.1);
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
      }
    }

    .upload-icon {
      font-size: 4rem;
      width: 4rem;
      height: 4rem;
      color: rgba(0, 71, 171, 0.7);
      margin-bottom: 1rem;
    }

    .drop-text {
      color: var(--text-primary);
      font-size: 1.1rem;
      margin-bottom: 0.5rem;
      font-weight: 400;
    }

    .drop-hint {
      color: var(--text-muted);
      font-size: 0.875rem;
      margin: 0;
    }

    .form-field-wrapper {
      margin-bottom: 1.5rem;
      
      .field-label {
        display: block;
        color: var(--text-primary);
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        letter-spacing: 0.3px;
      }
      
      .custom-input {
        width: 100%;
        padding: 0.875rem 1rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        color: var(--text-primary);
        font-size: 0.95rem;
        outline: none;
        transition: all 0.3s ease;
        font-family: inherit;
        
        &::placeholder {
          color: var(--text-muted);
        }
        
        &:hover {
          border-color: var(--border-hover);
          background: var(--bg-card-hover);
        }
        
        &:focus {
          border-color: var(--accent-primary);
          background: var(--bg-card-hover);
          box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.1);
        }
      }
      
      .field-hint {
        display: block;
        margin-top: 0.375rem;
        font-size: 0.75rem;
        color: var(--text-muted);
        font-style: italic;
      }
    }

    .checkbox-wrapper {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
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
        color: var(--text-primary);
        font-size: 0.95rem;
        cursor: pointer;
        
        .checkbox-icon {
          color: var(--accent-primary);
          font-size: 1.5rem;
          width: 1.5rem;
          height: 1.5rem;
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

    .upload-progress {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1.5rem;
      padding: 3rem 2rem;
      
      .progress-icon {
        font-size: 4rem;
        width: 4rem;
        height: 4rem;
        color: var(--accent-primary);
        animation: pulse 1.5s ease-in-out infinite;
      }
      
      h3 {
        color: var(--text-primary);
        font-size: 1.5rem;
        margin: 0;
        font-weight: 500;
      }
      
      mat-progress-bar {
        width: 100%;
      }
      
      .progress-detail {
        color: var(--text-secondary);
        margin: 0;
      }
    }

    @keyframes pulse {
      0%, 100% {
        opacity: 1;
        transform: scale(1);
      }
      50% {
        opacity: 0.5;
        transform: scale(1.1);
      }
    }

    .upload-complete {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 2rem;
      text-align: center;
      
      .success-icon {
        font-size: 5rem;
        width: 5rem;
        height: 5rem;
        color: var(--accent-primary);
        animation: scaleIn 0.5s ease-out;
        filter: drop-shadow(0 0 10px rgba(0, 217, 255, 0.5));
      }
      
      h3 {
        color: var(--text-primary);
        font-size: 1.75rem;
        margin: 0;
        font-weight: 500;
      }
      
      p {
        color: var(--text-secondary);
        margin: 0;
      }
      
      .processing-info {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin: 1.5rem 0;
        width: 100%;
        
        .info-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem;
          background: rgba(0, 71, 171, 0.15);
          border: 1px solid rgba(0, 71, 171, 0.3);
          border-radius: 8px;
          color: var(--accent-primary);
          font-size: 0.9rem;
          transition: all 0.3s ease;
          
          &:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-hover);
          }
          
          mat-icon {
            font-size: 1.25rem;
            width: 1.25rem;
            height: 1.25rem;
            color: var(--accent-primary);
          }
        }
      }
      
      .wait-message {
        font-size: 0.875rem;
        color: var(--text-muted);
        font-style: italic;
      }
    }

    @keyframes scaleIn {
      from {
        transform: scale(0);
        opacity: 0;
      }
      to {
        transform: scale(1);
        opacity: 1;
      }
    }

    ::ng-deep mat-dialog-actions {
      padding: 1rem 1.5rem !important;
      justify-content: flex-end;
      gap: 1rem;
      background: var(--bg-secondary);
      border-top: 1px solid var(--border-color);
      transition: background 0.3s ease, border-color 0.3s ease;
      
      button {
        border-radius: 10px;
        font-weight: 500;
        text-transform: none;
        padding: 0.625rem 1.5rem;
        transition: all 0.3s ease;
        
        &.mat-mdc-button {
          color: var(--text-secondary);
          
          &:hover {
            background: var(--bg-card-hover);
          }
        }
        
        &.mat-mdc-raised-button {
          background: var(--button-bg-primary) !important;
          color: var(--button-text) !important;
          
          * {
            color: var(--button-text) !important;
          }
          
          &:hover:not(:disabled) {
            background: var(--button-bg-hover) !important;
            box-shadow: var(--shadow-hover);
            transform: translateY(-1px);
          }
          
          &:disabled {
            background: var(--bg-card);
            color: var(--text-muted);
            
            * {
              color: var(--text-muted) !important;
            }
          }
          
          // Cancel button styling (same as Upload button)
          &.cancel-button {
            background: var(--button-bg-primary) !important;
            color: var(--button-text) !important;
            
            * {
              color: var(--button-text) !important;
            }
            
            &:hover {
              background: var(--button-bg-hover) !important;
              box-shadow: var(--shadow-hover);
              transform: translateY(-1px);
            }
          }
        }
      }
    }
  `]
})
export class UploadDialogComponent {
  private fb = inject(FormBuilder);
  private videoService = inject(VideoService);
  private dialogRef = inject(MatDialogRef<UploadDialogComponent>);

  uploadForm = this.fb.group({
    tags: [''],
    isPrivate: [false],  // Default to false = public
    allowedUsers: [''],
    scenario: ['']  // Analysis scenario (optional, falls back to default)
  });

  selectedFile = signal<File | null>(null);
  isDragOver = signal(false);
  uploading = signal(false);
  uploadComplete = signal(false);
  uploadPhase = signal<'requesting' | 'uploading'>('requesting');
  error = signal<string | null>(null);

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.handleFile(files[0]);
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFile(input.files[0]);
    }
  }

  handleFile(file: File) {
    // Validate file type - only MP4 is supported by NVIDIA Cosmos Reason
    const fileName = file.name.toLowerCase();
    const isMP4ByExtension = fileName.endsWith('.mp4');
    const isMP4ByType = file.type === 'video/mp4';
    
    if (!isMP4ByExtension && !isMP4ByType) {
      this.error.set('Only MP4 video format is supported (required by NVIDIA Cosmos VLM)');
      return;
    }

    // Validate file size (25MB)
    const maxSize = 25 * 1024 * 1024;
    if (file.size > maxSize) {
      this.error.set('File size exceeds 25MB limit');
      return;
    }

    this.selectedFile.set(file);
    this.error.set(null);
  }

  canUpload(): boolean {
    return this.selectedFile() !== null && this.uploadForm.valid;
  }

  async upload() {
    if (!this.canUpload() || !this.selectedFile()) return;

    this.uploading.set(true);
    this.uploadPhase.set('requesting');
    this.error.set(null);

    try {
      const file = this.selectedFile()!;
      const formValue = this.uploadForm.value;

      // Parse tags and allowed users
      const tags = formValue.tags 
        ? formValue.tags.split(',').map((t: string) => t.trim()).filter((t: string) => t)
        : [];
      
      const allowedUsers = formValue.allowedUsers
        ? formValue.allowedUsers.split(',').map((u: string) => u.trim()).filter((u: string) => u)
        : [];

      // Upload directly to backend (backend proxies to S3)
      console.log('Uploading video:', file.name);
      this.uploadPhase.set('uploading');
      
      // NEW LOGIC: isPrivate checkbox → invert to is_public for backend
      // isPrivate=false → is_public=true (default, public)
      // isPrivate=true → is_public=false (private)
      const isPublic = !formValue.isPrivate;
      
      const scenario = formValue.scenario || '';
      
      const response = await this.videoService.uploadVideo(
        file,
        isPublic,
        tags,
        allowedUsers,
        scenario
      ).toPromise();
      
      console.log('Upload completed successfully:', response);

      // Success!
      this.uploading.set(false);
      this.uploadComplete.set(true);

    } catch (err: any) {
      console.error('Upload failed:', err);
      this.uploading.set(false);
      
      // Extract meaningful error message
      let errorMessage = 'Upload failed. Please try again.';
      if (err.error?.detail) {
        errorMessage = err.error.detail;
      } else if (err.message) {
        errorMessage = err.message;
      } else if (err.error?.message) {
        errorMessage = err.error.message;
      }
      
      this.error.set(errorMessage);
    }
  }

  uploadPhaseText(): string {
    return 'Uploading to VAST...';
  }

  uploadPhaseDetail(): string {
    return 'Transferring video file to S3 storage';
  }

  close() {
    this.dialogRef.close();
  }
}

