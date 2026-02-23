import { ChangeDetectionStrategy, Component, input, output, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Collection } from '../../../shared/models/collections.model';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-collection-card',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule],
  templateUrl: './collection-card.component.html',
  styleUrls: ['./collection-card.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CollectionCardComponent {
  collection = input.required<Collection>();
  className = input<string>('');
  upload = output<Collection>();
  delete = output<Collection>();
  doubleClick = output<Collection>();

  onUpload(event: Event) {
    event.stopPropagation();
    this.upload.emit(this.collection());
  }

  onDelete(event: Event) {
    event.stopPropagation();
    this.delete.emit(this.collection());
  }

  onDoubleClick() {
    this.doubleClick.emit(this.collection());
  }

  collectionName = computed(() => this.collection().title);

  entityCount = computed(() => {
    // Match both "entities" and "files" (backend may send either)
    const match = this.collection().description?.match(/(\d+)\s+(?:entities|files)/);
    return match ? parseInt(match[1], 10) : 0;
  });

  /** Description with "entities" replaced by "files" for display */
  descriptionForDisplay = computed(() =>
    (this.collection().description || '').replace(/entities/g, 'files')
  );

  fileCountText = computed(() => {
    const count = this.entityCount();
    if (count === 1) return '1 file';
    return `${count} files`;
  });
}
