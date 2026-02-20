import { Component, signal, input, output, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

export interface FileInputConfig {
  accept?: string;
  maxSizeInMB?: number;
  disabled?: boolean;
}

export interface FileValidationError {
  type: 'size' | 'type' | 'general';
  message: string;
}

@Component({
  selector: 'app-file-input',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  templateUrl: './file-input.component.html',
  styleUrls: ['./file-input.component.scss']
})
export class FileInputComponent {
  @ViewChild('fileInput', { static: true }) fileInput!: ElementRef<HTMLInputElement>;

  // Configuration inputs
  config = input<FileInputConfig>({
    accept: '.pdf,.txt,.doc,.docx,.md,.json,.xml,.csv,.xlsx,.xls',
    maxSizeInMB: 50,
    disabled: false
  });

  // State
  selectedFile = signal<File | null>(null);
  dragOver = signal<boolean>(false);
  isDisabled = signal<boolean>(false);

  // Events
  fileSelected = output<File>();
  fileRemoved = output<void>();
  validationError = output<FileValidationError>();

  /**
   * Handles file selection from input element
   */
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      this.processFile(file);
    }
    // Reset input value to allow selecting the same file again
    input.value = '';
  }

  /**
   * Handles drag over event
   */
  onDragOver(event: DragEvent): void {
    if (this.isDisabled()) return;

    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(true);
  }

  /**
   * Handles drag leave event
   */
  onDragLeave(event: DragEvent): void {
    if (this.isDisabled()) return;

    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(false);
  }

  /**
   * Handles file drop
   */
  onDrop(event: DragEvent): void {
    if (this.isDisabled()) return;

    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(false);

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.processFile(files[0]);
    }
  }

  /**
   * Opens file browser
   */
  browseFiles(): void {
    if (this.isDisabled()) return;
    this.fileInput.nativeElement.click();
  }

  /**
   * Removes the selected file
   */
  removeFile(): void {
    if (this.isDisabled()) return;

    this.selectedFile.set(null);
    this.fileRemoved.emit();
  }

  /**
   * Processes and validates the selected file
   */
  private processFile(file: File): void {
    // Validate file size
    const maxSizeInBytes = (this.config().maxSizeInMB || 50) * 1024 * 1024;
    if (file.size > maxSizeInBytes) {
      const error: FileValidationError = {
        type: 'size',
        message: `File size exceeds ${this.config().maxSizeInMB}MB limit`
      };
      this.validationError.emit(error);
      return;
    }

    // Validate file type if accept is specified
    if (this.config().accept) {
      const acceptedTypes = this.config().accept!.split(',').map(type => type.trim());
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      const mimeType = file.type.toLowerCase();

      const isAccepted = acceptedTypes.some(acceptedType => {
        if (acceptedType.startsWith('.')) {
          return fileExtension === acceptedType.toLowerCase();
        } else {
          return mimeType.includes(acceptedType.replace('*', '').toLowerCase());
        }
      });

      if (!isAccepted) {
        const error: FileValidationError = {
          type: 'type',
          message: `File type not supported. Accepted types: ${this.config().accept}`
        };
        this.validationError.emit(error);
        return;
      }
    }

    // File is valid
    this.selectedFile.set(file);
    this.fileSelected.emit(file);
  }

  /**
   * Gets the file size in human readable format
   */
  getFileSizeString(size: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let unitIndex = 0;
    let fileSize = size;

    while (fileSize >= 1024 && unitIndex < units.length - 1) {
      fileSize /= 1024;
      unitIndex++;
    }

    return `${fileSize.toFixed(1)} ${units[unitIndex]}`;
  }

  /**
   * Clears the selected file programmatically
   */
  clearFile(): void {
    this.selectedFile.set(null);
  }

  /**
   * Sets disabled state
   */
  setDisabled(disabled: boolean): void {
    this.isDisabled.set(disabled);
  }
}