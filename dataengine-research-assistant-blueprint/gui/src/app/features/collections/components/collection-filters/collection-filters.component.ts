import { ChangeDetectionStrategy, Component, inject, signal, computed, effect, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatChipSet, MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { CollectionsService } from '../../services/collections.service';
import { CollectionFilter } from '../../../shared/models/collections.model';

@Component({
  selector: 'app-collection-filters',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatChipsModule,
    MatIconModule
  ],
  templateUrl: './collection-filters.component.html',
  styleUrls: ['./collection-filters.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CollectionFiltersComponent {
  private collectionsService = inject(CollectionsService);

  filterChange = output<CollectionFilter>();

  searchControl = new FormControl('');

  currentFilter = computed(() => {
    const searchTerm = this.searchControl.value?.trim() || undefined;

    return {
      searchTerm
    } as CollectionFilter;
  });

  constructor() {
    effect(() => {
      const filter = this.currentFilter();
      this.filterChange.emit(filter);
    });
  }

  onClearSearch() {
    this.searchControl.setValue('');
  }
}
