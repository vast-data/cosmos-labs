import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { CollectionsService } from '../../services/collections.service';
import { CreateCollectionResponse } from '../../../shared/models/collections.model';

export interface CreateCollectionDialogResult {
  success: boolean;
  cancelled?: boolean;
  collectionName?: string;
}

@Component({
  selector: 'app-create-collection-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatCheckboxModule,
    MatSnackBarModule
  ],
  templateUrl: './create-collection-dialog.component.html',
  styleUrls: ['./create-collection-dialog.component.scss']
})
export class CreateCollectionDialogComponent {
  private dialogRef = inject<MatDialogRef<CreateCollectionDialogComponent, CreateCollectionDialogResult>>(MatDialogRef);
  private collectionsService = inject(CollectionsService);
  private snackBar = inject(MatSnackBar);

  collectionName = signal<string>('');
  isPublic = signal<boolean>(true);
  isCreating = signal<boolean>(false);
  error = signal<string | null>(null);

  canCreate(): boolean {
    return this.collectionName().trim().length > 0 && !this.isCreating();
  }

  onCreate(): void {
    const name = this.collectionName().trim();

    if (!name) {
      this.error.set('Collection name is required');
      return;
    }

    this.isCreating.set(true);
    this.error.set(null);

    this.collectionsService.createCollection({ collection_name: name, is_public: this.isPublic() }).subscribe({
      next: (response: CreateCollectionResponse) => {
        this.isCreating.set(false);

        this.snackBar.open('Collection created successfully!', 'Close', {
          duration: 3000
        });

        this.dialogRef.close({
          success: true,
          collectionName: name
        });
      },
      error: (err: unknown) => {
        this.isCreating.set(false);

        const errorMessage = this.extractErrorMessage(err);
        this.error.set(errorMessage);

        this.snackBar.open(errorMessage, 'Close', {
          duration: 5000
        });
      }
    });
  }

  onCancel(): void {
    this.dialogRef.close({
      success: false,
      cancelled: true
    });
  }

  private extractErrorMessage(err: unknown): string {
    if (err && typeof err === 'object') {
      const error = err as { error?: { message?: string }; message?: string };
      return error.error?.message ?? error.message ?? 'Failed to create collection. Please try again.';
    }
    return 'Failed to create collection. Please try again.';
  }
}

