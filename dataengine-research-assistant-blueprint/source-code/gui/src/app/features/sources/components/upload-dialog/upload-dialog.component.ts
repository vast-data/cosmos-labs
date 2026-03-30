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
  responses?: UploadDocumentResponse[];
  fileNames?: string[];
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

  collectionName = signal<string>('');
  selectedFiles = signal<File[]>([]);
  isUploading = signal<boolean>(false);
  uploadProgress = signal<number>(0);
  uploadedCount = signal<number>(0);

  fileInputConfig: FileInputConfig = {
    accept: '.pdf,.md,.txt,.doc,.docx,.json,.xml,.csv,.xlsx,.xls',
    maxSizeInMB: 50,
    disabled: false,
    multiple: true
  };

  ngOnInit(): void {
    if (this.data.collectionName) {
      this.collectionName.set(this.data.collectionName);
    }
  }

  onFilesSelected(files: File[]): void {
    this.selectedFiles.set(files);
  }

  onFileRemoved(): void {
    this.selectedFiles.set([]);
  }

  onValidationError(error: FileValidationError): void {
    this.snackBar.open(error.message, 'Close', { duration: 3000 });
  }

  uploadFiles(): void {
    const files = this.selectedFiles();
    const collectionName = this.collectionName();
    if (files.length === 0 || !collectionName) return;

    this.isUploading.set(true);
    this.uploadProgress.set(0);
    this.uploadedCount.set(0);
    this.fileInputComponent.setDisabled(true);

    const responses: UploadDocumentResponse[] = [];
    const fileNames: string[] = [];
    let completed = 0;
    let failed = 0;

    for (const file of files) {
      const uploadData: UploadDocumentData = { collection_name: collectionName, file };
      this.sourcesApiService.uploadDocument(uploadData).subscribe({
        next: (response) => {
          responses.push(response);
          fileNames.push(file.name);
          completed++;
          this.uploadedCount.set(completed);
          this.uploadProgress.set(Math.round(((completed + failed) / files.length) * 100));
          if (completed + failed === files.length) this.onAllUploadsComplete(responses, fileNames, failed);
        },
        error: () => {
          failed++;
          this.uploadProgress.set(Math.round(((completed + failed) / files.length) * 100));
          if (completed + failed === files.length) this.onAllUploadsComplete(responses, fileNames, failed);
        }
      });
    }
  }

  private onAllUploadsComplete(responses: UploadDocumentResponse[], fileNames: string[], failed: number): void {
    this.isUploading.set(false);
    this.fileInputComponent.setDisabled(false);

    if (failed > 0) {
      this.snackBar.open(`${fileNames.length} uploaded, ${failed} failed`, 'Close', { duration: 5000 });
    } else {
      this.snackBar.open(`${fileNames.length} file(s) uploaded successfully!`, 'Close', { duration: 3000 });
    }

    this.dialogRef.close({ success: true, responses, fileNames });
  }

  cancel(): void {
    if (this.fileInputComponent) this.fileInputComponent.clearFile();
    this.dialogRef.close({ success: false, cancelled: true });
  }
}