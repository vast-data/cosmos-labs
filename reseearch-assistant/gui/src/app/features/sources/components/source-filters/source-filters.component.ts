import { ChangeDetectionStrategy, Component, computed, effect, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { SourceFilter } from '../../../shared/models/sources.model';

@Component({
  selector: 'app-source-filters',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule
  ],
  templateUrl: './source-filters.component.html',
  styleUrls: ['./source-filters.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SourceFiltersComponent {
  filterChange = output<SourceFilter>();

  searchControl = new FormControl('');

  currentFilter = computed(() => {
    const searchTerm = this.searchControl.value?.trim() || undefined;
    return {
      searchTerm
    } as SourceFilter;
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
