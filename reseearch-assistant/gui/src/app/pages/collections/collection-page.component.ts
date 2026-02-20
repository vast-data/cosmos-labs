import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialog } from '@angular/material/dialog';
import { CollectionListComponent } from '../../features/collections/components/collection-list/collection-list.component';
import { CollectionsService } from '../../features/collections/services/collections.service';
import { 
  UploadDialogComponent, 
  UploadDialogData, 
  UploadDialogResult 
} from '../../features/sources/components/upload-dialog/upload-dialog.component';
import { Collection } from '../../features/shared/models/collections.model';

@Component({
  selector: 'app-collection-page',
  standalone: true,
  imports: [CommonModule, CollectionListComponent],
  templateUrl: './collection-page.component.html',
  styleUrls: ['./collection-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CollectionPageComponent {
  private dialog = inject(MatDialog);
  private collectionsService = inject(CollectionsService);

  onUploadToCollection(collection: Collection) {
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

