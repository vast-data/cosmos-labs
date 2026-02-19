import { ChangeDetectionStrategy, Component, inject, computed, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { SourcesService } from '../../services/sources.service';
import { SourceCardComponent } from '../source-card/source-card.component';
import { SourceFiltersComponent } from '../source-filters/source-filters.component';
import { SourceFilter, Document } from '../../../shared/models/sources.model';
import { map, filter, distinctUntilChanged, takeUntil } from 'rxjs/operators';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-collection-sources',
  standalone: true,
  imports: [
    CommonModule,
    SourceCardComponent,
    SourceFiltersComponent
  ],
  templateUrl: './collection-sources.component.html',
  styleUrls: ['./collection-sources.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CollectionSourcesComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sourcesService = inject(SourcesService);
  private destroy$ = new Subject<void>();

  collectionName = computed(() => this.sourcesService.currentCollection());

  sources = computed(() => this.sourcesService.filteredDocuments());
  totalDocuments = computed(() => this.sourcesService.totalDocuments());
  isLoading = computed(() => this.sourcesService.isLoading());
  hasActiveFilters = computed(() => {
    const filter = this.sourcesService.currentFilter();
    return !!(filter?.searchTerm && filter.searchTerm.length > 0);
  });

  ngOnInit() {
    this.route.params
      .pipe(
        map(params => params['id'] as string),
        filter(collection => !!collection),
        distinctUntilChanged(),
        takeUntil(this.destroy$)
      )
      .subscribe(collection => {
        this.sourcesService.loadSources(collection);
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onFilterChange(filter: SourceFilter) {
    this.sourcesService.setFilter(filter);
  }

  onSourceEdit(source: Document) {
    // TODO: Implement edit functionality
    console.log('Edit source:', source);
  }

  onSourceDelete(source: Document) {
    this.sourcesService.deleteDocument(source.document_name).subscribe({
      next: () => {
        const collection = this.sourcesService.currentCollection();
        if (collection) {
          this.sourcesService.loadSources(collection);
        }
      },
      error: (error) => {
        console.error('Failed to delete source:', error);
      }
    });
  }

  navigateToCollections() {
    this.router.navigate(['/collections']);
  }

  trackByDocumentName(index: number, document: Document): string {
    return document.document_name;
  }
}
