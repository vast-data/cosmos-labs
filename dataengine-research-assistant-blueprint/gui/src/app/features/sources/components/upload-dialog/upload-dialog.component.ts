import { Component, inject, signal, ViewChild, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { FileInputComponent, FileInputConfig, FileValidationError } from '../../../shared/index';
import { SourcesApiService } from '../../services/sources-api.service';
import { UploadDocumentData, UploadDocumentResponse } from '../../../shared/models/sources.model';

export interface UploadDialogData {
  collectionName: string;
}

export interface UploadDialogResult {
  success: boolean;
  cancelled?: boolean;
  response?: UploadDocumentResponse;
  fileName?: string;
}

@Component({
  selector: 'app-upload-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatDialogModule,
    FileInputComponent
  ],
  templateUrl: './upload-dialog.component.html',
  styleUrls: ['./upload-dialog.component.scss']
})
export class UploadDialogComponent implements OnInit {
  @ViewChild(FileInputComponent) fileInputComponent!: FileInputComponent;

  private dialogRef = inject<MatDialogRef<UploadDialogComponent, UploadDialogResult>>(MatDialogRef);
  private data = inject<UploadDialogData>(MAT_DIALOG_DATA);
  private sourcesApiService = inject(SourcesApiService);
  private snackBar = inject(MatSnackBar);

  // Input: collection name (passed via dialog config data)
  collectionName = signal<string>('');

  // Component state
  selectedFile = signal<File | null>(null);
  isUploading = signal<boolean>(false);
  uploadProgress = signal<number>(0);

  // File input configuration - restricted to PDF and MD files only
  fileInputConfig: FileInputConfig = {
    accept: '.pdf,.md',
    maxSizeInMB: 50,
    disabled: false
  };

  ngOnInit(): void {
    // Get collection name from injected dialog data
    if (this.data.collectionName) {
      this.collectionName.set(this.data.collectionName);
    }
  }

  /**
   * Handles file selection from file input component
   */
  onFileSelected(file: File): void {
    this.selectedFile.set(file);
  }

  /**
   * Handles file removal from file input component
   */
  onFileRemoved(): void {
    this.selectedFile.set(null);
  }

  /**
   * Handles validation errors from file input component
   */
  onValidationError(error: FileValidationError): void {
    this.snackBar.open(error.message, 'Close', {
      duration: 3000
    });
  }

  /**
   * Uploads the selected file
   */
  uploadFile(): void {
    const file = this.selectedFile();
    const collectionName = this.collectionName();

    if (!file || !collectionName) {
      return;
    }

    this.isUploading.set(true);
    this.uploadProgress.set(0);

    // Disable file input during upload
    this.fileInputComponent.setDisabled(true);

    const uploadData: UploadDocumentData = {
      collection_name: collectionName,
      file: file
    };

    this.sourcesApiService.uploadDocument(uploadData).subscribe({
      next: (response: UploadDocumentResponse) => {
        this.isUploading.set(false);
        this.uploadProgress.set(100);

        // Re-enable file input
        this.fileInputComponent.setDisabled(false);

        // Show success message
        this.snackBar.open('File uploaded successfully!', 'Close', {
          duration: 3000
        });

        // Close dialog with success result
        this.dialogRef.close({
          success: true,
          response: response as UploadDocumentResponse,
          fileName: file.name
        });
      },
      error: (error: any) => {
        this.isUploading.set(false);
        this.uploadProgress.set(0);

        // Re-enable file input
        this.fileInputComponent.setDisabled(false);

        // Show error message
        const errorMessage = error.error?.message || 'Upload failed. Please try again.';
        this.snackBar.open(errorMessage, 'Close', {
          duration: 5000
        });
      }
    });
  }

  /**
   * Cancels the upload and closes the dialog
   */
  cancel(): void {
    // Clear file selection if any
    if (this.fileInputComponent) {
      this.fileInputComponent.clearFile();
    }

    this.dialogRef.close({
      success: false,
      cancelled: true
    });
  }
}