import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Collection } from '../../../shared/models/collections.model';

export interface DeleteCollectionDialogData {
  collection: Collection;
}

@Component({
  selector: 'app-delete-collection-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule
  ],
  template: `
    <div class="delete-dialog">
      <div class="dialog-header">
        <mat-icon class="warning-icon">warning</mat-icon>
        <h2>Delete Collection</h2>
      </div>
      
      <div class="dialog-content">
        <p>Are you sure you want to delete the collection <strong>{{ data.collection.title }}</strong>?</p>
        <p class="warning-text">This action cannot be undone. All documents in this collection will be permanently deleted.</p>
      </div>
      
      <div class="dialog-actions">
        <button mat-button (click)="onCancel()">Cancel</button>
        <button mat-flat-button color="warn" (click)="onConfirm()">Delete</button>
      </div>
    </div>
  `,
  styles: [`
    .delete-dialog {
      padding: 1.5rem;
      background: #16233F;
      color: #E8EBEC;
    }

    .dialog-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1.5rem;

      .warning-icon {
        color: #FF6B6B;
        font-size: 1.5rem;
        width: 1.5rem;
        height: 1.5rem;
      }

      h2 {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
      }
    }

    .dialog-content {
      margin-bottom: 1.5rem;

      p {
        margin: 0 0 0.75rem 0;
        line-height: 1.5;
      }

      .warning-text {
        color: #FF6B6B;
        font-size: 0.875rem;
      }

      strong {
        color: #54B2E7;
      }
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;

      button {
        min-width: 80px;
      }
    }
  `]
})
export class DeleteCollectionDialogComponent {
  private dialogRef = inject(MatDialogRef<DeleteCollectionDialogComponent>);
  data = inject<DeleteCollectionDialogData>(MAT_DIALOG_DATA);

  onCancel() {
    this.dialogRef.close({ confirmed: false });
  }

  onConfirm() {
    this.dialogRef.close({ confirmed: true });
  }
}

