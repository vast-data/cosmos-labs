import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  output,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatMenuModule } from '@angular/material/menu';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { CollectionsService } from '../../../collections/services/collections.service';
import { Collection } from '../../../shared/models/collections.model';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  UploadDialogComponent,
  UploadDialogData,
  UploadDialogResult
} from '../../../sources/components/upload-dialog/upload-dialog.component';

@Component({
  selector: 'app-collection-selector',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatMenuModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
  ],
  templateUrl: './collection-selector.component.html',
  styleUrl: './collection-selector.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CollectionSelectorComponent {
  private collectionsService = inject(CollectionsService);
  private dialog = inject(MatDialog);

  collectionSelected = output<Collection>();

  searchControl = new FormControl('');
  private selectedCollectionSignal = signal<Collection | null>(null);

  collections = this.collectionsService.collections;
  isLoading = this.collectionsService.isLoading;

  selectedCollection = computed(() => this.selectedCollectionSignal());

  formChangesSignal = toSignal(this.searchControl.valueChanges);

  filteredCollections = computed(() => {
    const collections = this.collections();
    const searchTerm = this.formChangesSignal()?.toLowerCase().trim();

    if (!searchTerm) {
      return collections;
    }

    return collections.filter(
      (collection) =>
        collection.id.toLowerCase().includes(searchTerm)
    );
  });

  onSelectCollection(collection: Collection): void {
    this.selectedCollectionSignal.set(collection);
    this.collectionSelected.emit(collection);
    this.searchControl.setValue('');
  }

  onClearSearch(): void {
    this.searchControl.setValue('');
  }

  onMenuOpened(): void {
    this.searchControl.setValue('');
  }

  descriptionDisplay(desc: string | undefined): string {
    return (desc || '').replace(/entities/g, 'files');
  }

  onUploadToCollection(collection: Collection, event: Event): void {
    event.stopPropagation();

    const collectionName = collection.id.split('__')[1] || collection.id;

    const dialogRef = this.dialog.open<UploadDialogComponent, UploadDialogData, UploadDialogResult>(
      UploadDialogComponent,
      {
        data: { collectionName },
        width: '500px',
        disableClose: false
      }
    );

    dialogRef.afterClosed().subscribe(result => {
      if (result?.success) {
        this.collectionsService.loadCollections();
      }
    });
  }
}
