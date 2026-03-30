import { ChangeDetectionStrategy, Component, inject, computed, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CollectionsService } from '../../services/collections.service';
import { CollectionCardComponent } from '../collection-card/collection-card.component';
import { CollectionFiltersComponent } from '../collection-filters/collection-filters.component';
import { Collection, CollectionFilter } from '../../../shared/models/collections.model';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { CreateCollectionDialogComponent } from '../create-collection-dialog/create-collection-dialog.component';
import { DeleteCollectionDialogComponent } from '../delete-collection-dialog/delete-collection-dialog.component';

@Component({
  selector: 'app-collection-list',
  standalone: true,
  imports: [
    CommonModule,
    CollectionCardComponent,
    CollectionFiltersComponent,
    MatSnackBarModule
  ],
  templateUrl: './collection-list.component.html',
  styleUrls: ['./collection-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CollectionListComponent {
  private router = inject(Router);
  private collectionsService = inject(CollectionsService);
  private dialogService = inject(MatDialog);
  private snackBar = inject(MatSnackBar);

  collectionsChange = output<Collection[]>();
  uploadToCollection = output<Collection>();

  collections = computed(() => this.collectionsService.filteredCollections());
  isLoading = computed(() => this.collectionsService.isLoading());
  hasActiveFilters = computed(() => {
    const filter = this.collectionsService.currentFilter();
    return !!(filter?.searchTerm);
  });

  onFilterChange(filter: CollectionFilter) {
    this.collectionsService.setFilter(filter);
  }

  onCollectionDoubleClick(collection: Collection) {
    const collectionName = collection.id.split('__')[1] || collection.id;
    this.router.navigate(['/collections', collectionName]);
  }

  onCollectionUpload(collection: Collection) {
    this.uploadToCollection.emit(collection);
  }

  onCollectionDelete(collection: Collection) {
    const dialogRef = this.dialogService.open(DeleteCollectionDialogComponent, {
      width: '400px',
      hasBackdrop: true,
      disableClose: false,
      data: { collection }
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result?.confirmed) {
        const collectionTitle = collection.title;
        this.collectionsService.deleteCollection(collection.id).subscribe({
          next: () => {
            // Show success message
            this.snackBar.open(`Collection "${collectionTitle}" deleted successfully!`, 'Close', {
              duration: 3000
            });
            // Reload collections after successful deletion
            this.collectionsService.loadCollections();
          },
          error: (error) => {
            console.error('Error deleting collection:', error);
            this.snackBar.open('Failed to delete collection. Please try again.', 'Close', {
              duration: 5000
            });
          }
        });
      }
    });
  }

  onCreateCollection(): void {
    const dialogRef = this.dialogService.open(CreateCollectionDialogComponent, {
      width: '500px',
      hasBackdrop: true,
      disableClose: false
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result?.success) {
        // Reload collections after successful creation
        this.collectionsService.loadCollections();
      }
    });
  }

  trackByCollectionName(index: number, collection: Collection): string {
    return collection.id;
  }
}
