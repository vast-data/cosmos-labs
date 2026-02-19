import { Injectable, inject, signal, computed } from '@angular/core';
import { SourcesApiService } from './sources-api.service';
import { SourcesResponse, SourceFilter, CreateDocumentData, UpdateDocumentData } from '../../shared/models/sources.model';

@Injectable({
  providedIn: 'root'
})
export class SourcesService {
  private apiService = inject(SourcesApiService);

  private sourcesResponseSignal = signal<SourcesResponse | null>(null);
  private isLoadingSignal = signal(false);
  private hasLoadedOnceSignal = signal(false);
  private errorSignal = signal<string | null>(null);
  private currentCollectionSignal = signal<string>('');

  documents = computed(() => this.sourcesResponseSignal()?.documents || []);
  totalDocuments = computed(() => this.sourcesResponseSignal()?.total_documents || '0');
  isLoading = computed(() => this.isLoadingSignal() && !this.hasLoadedOnceSignal());
  error = computed(() => this.errorSignal());
  currentCollection = computed(() => this.currentCollectionSignal());

  filteredDocuments = computed(() => {
    const documents = this.documents();
    const filter = this.currentFilter();

    if (!filter) return documents;

    let filtered = documents;

    if (filter.searchTerm) {
      const searchLower = filter.searchTerm.toLowerCase();
      filtered = filtered.filter(
        (document) =>
          document.document_name.toLowerCase().includes(searchLower)
      );
    }

    return filtered;
  });

  private currentFilterSignal = signal<SourceFilter | undefined>(undefined);
  currentFilter = computed(() => this.currentFilterSignal());

  loadSources(collectionName: string) {
    if (!collectionName) return;

    this.currentCollectionSignal.set(collectionName);
    this.isLoadingSignal.set(true);
    this.errorSignal.set(null);

    this.apiService.getSources(collectionName).subscribe({
      next: (response) => {
        this.sourcesResponseSignal.set(response);
        this.isLoadingSignal.set(false);
        this.hasLoadedOnceSignal.set(true);
      },
      error: (error) => {
        this.errorSignal.set(error.message || 'Failed to load sources');
        this.isLoadingSignal.set(false);
      }
    });
  }

  setFilter(filter: SourceFilter) {
    this.currentFilterSignal.set(filter);
  }

  createDocument(data: CreateDocumentData) {
    const collectionName = this.currentCollection();
    return this.apiService.createDocument(collectionName, data);
  }

  updateDocument(documentName: string, data: UpdateDocumentData) {
    const collectionName = this.currentCollection();
    return this.apiService.updateDocument(collectionName, documentName, data);
  }

  deleteDocument(documentName: string) {
    const collectionName = this.currentCollection();
    return this.apiService.deleteDocument(collectionName, documentName);
  }
}
