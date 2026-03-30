import { Component, signal, input, output, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

export interface FileInputConfig {
  accept?: string;
  maxSizeInMB?: number;
  disabled?: boolean;
  multiple?: boolean;
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
  @ViewChild('folderInput', { static: false }) folderInput?: ElementRef<HTMLInputElement>;

  config = input<FileInputConfig>({
    accept: '.pdf,.txt,.doc,.docx,.md,.json,.xml,.csv,.xlsx,.xls',
    maxSizeInMB: 50,
    disabled: false,
    multiple: true
  });

  selectedFiles = signal<File[]>([]);
  dragOver = signal<boolean>(false);
  isDisabled = signal<boolean>(false);

  /** @deprecated Use filesSelected instead */
  fileSelected = output<File>();
  filesSelected = output<File[]>();
  fileRemoved = output<void>();
  validationError = output<FileValidationError>();

  get selectedFile(): File | null {
    const files = this.selectedFiles();
    return files.length > 0 ? files[0] : null;
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;
    this.processFiles(Array.from(input.files));
    input.value = '';
  }

  onDragOver(event: DragEvent): void {
    if (this.isDisabled()) return;
    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(true);
  }

  onDragLeave(event: DragEvent): void {
    if (this.isDisabled()) return;
    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(false);
  }

  onDrop(event: DragEvent): void {
    if (this.isDisabled()) return;
    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(false);

    const items = event.dataTransfer?.items;
    if (items) {
      const entries: FileSystemEntry[] = [];
      for (let i = 0; i < items.length; i++) {
        const entry = items[i].webkitGetAsEntry?.();
        if (entry) entries.push(entry);
      }
      if (entries.length > 0) {
        this.readEntries(entries);
        return;
      }
    }

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.processFiles(Array.from(files));
    }
  }

  browseFiles(): void {
    if (this.isDisabled()) return;
    this.fileInput.nativeElement.click();
  }

  browseFolder(): void {
    if (this.isDisabled()) return;
    this.folderInput?.nativeElement.click();
  }

  removeFile(index?: number): void {
    if (this.isDisabled()) return;
    if (index !== undefined) {
      const current = [...this.selectedFiles()];
      current.splice(index, 1);
      this.selectedFiles.set(current);
      if (current.length === 0) this.fileRemoved.emit();
    } else {
      this.selectedFiles.set([]);
      this.fileRemoved.emit();
    }
  }

  private async readEntries(entries: FileSystemEntry[]): Promise<void> {
    const files: File[] = [];
    const readEntry = (entry: FileSystemEntry): Promise<void> => {
      return new Promise(resolve => {
        if (entry.isFile) {
          (entry as FileSystemFileEntry).file(f => { files.push(f); resolve(); });
        } else if (entry.isDirectory) {
          const reader = (entry as FileSystemDirectoryEntry).createReader();
          reader.readEntries(async subEntries => {
            for (const sub of subEntries) await readEntry(sub);
            resolve();
          });
        } else {
          resolve();
        }
      });
    };
    for (const entry of entries) await readEntry(entry);
    if (files.length > 0) this.processFiles(files);
  }

  private processFiles(files: File[]): void {
    const maxSizeInBytes = (this.config().maxSizeInMB || 50) * 1024 * 1024;
    const acceptedTypes = this.config().accept?.split(',').map(t => t.trim()) ?? [];
    const valid: File[] = [];

    for (const file of files) {
      if (file.size > maxSizeInBytes) {
        this.validationError.emit({ type: 'size', message: `${file.name} exceeds ${this.config().maxSizeInMB}MB limit` });
        continue;
      }
      if (acceptedTypes.length > 0) {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        const mime = file.type.toLowerCase();
        const accepted = acceptedTypes.some(t =>
          t.startsWith('.') ? ext === t.toLowerCase() : mime.includes(t.replace('*', '').toLowerCase())
        );
        if (!accepted) {
          this.validationError.emit({ type: 'type', message: `${file.name}: unsupported type. Accepted: ${this.config().accept}` });
          continue;
        }
      }
      valid.push(file);
    }

    if (valid.length === 0) return;

    if (this.config().multiple) {
      const current = [...this.selectedFiles(), ...valid];
      this.selectedFiles.set(current);
      this.filesSelected.emit(current);
    } else {
      this.selectedFiles.set([valid[0]]);
      this.fileSelected.emit(valid[0]);
    }
  }

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

  clearFile(): void {
    this.selectedFiles.set([]);
  }

  setDisabled(disabled: boolean): void {
    this.isDisabled.set(disabled);
  }
}