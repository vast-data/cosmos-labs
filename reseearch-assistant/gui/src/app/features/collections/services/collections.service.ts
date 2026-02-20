import { Injectable, inject, signal, computed, effect } from '@angular/core';
import { CollectionsApiService } from './collections-api.service';
import { Collection, CollectionsResponse, CollectionFilter } from '../../shared/models/collections.model';
import { AuthService } from '../../auth/services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class CollectionsService {
  private apiService = inject(CollectionsApiService);
  private authService = inject(AuthService);

  private collectionsResponseSignal = signal<CollectionsResponse | null>(null);
  private isLoadingSignal = signal(false);
  private hasLoadedOnceSignal = signal(false);
  private errorSignal = signal<string | null>(null);
  private previousTokenSignal = signal<string | null>(null);

  /**
   * Extracts the collection title from the collection id.
   * If the id contains '__', returns the part after '__', otherwise returns the id.
   */
  getCollectionTitle(collectionId: string): string {
    const parts = collectionId.split('__');
    return parts.length > 1 ? parts[1] : collectionId;
  }

  /**
   * Checks if a collection is private based on its id.
   * Returns true if the id has a prefix before '__'.
   */
  isCollectionPrivate(collectionId: string): boolean {
    return collectionId.includes('__');
  }

  collections = computed(() => {
    const response = this.collectionsResponseSignal();
    if (!response?.collections) return [];

    return response.collections.map((collection): Collection => ({
      ...collection,
      title: this.getCollectionTitle(collection.id),
      private: this.isCollectionPrivate(collection.id)
    }));
  });
  isLoading = computed(() => this.isLoadingSignal() && !this.hasLoadedOnceSignal());
  error = computed(() => this.errorSignal());

  filteredCollections = computed(() => {
    const collections = this.collections();
    const filter = this.currentFilter();

    if (!filter) return collections;

    let filtered = collections;

    if (filter.searchTerm) {
      const searchLower = filter.searchTerm.toLowerCase();
      filtered = filtered.filter(
        (collection) =>
          collection.id.toLowerCase().includes(searchLower) ||
          collection.description.toLowerCase().includes(searchLower)
      );
    }

    return filtered;
  });

  private currentFilterSignal = signal<CollectionFilter | undefined>(undefined);
  currentFilter = computed(() => this.currentFilterSignal());

  // Available tags for filtering (not used in current API structure)
  availableTags = computed(() => {
    // Tags are not part of the current API response structure
    return [];
  });

  loadCollections() {
    const token = this.authService.token();
    console.log('CollectionsService.loadCollections() called, token =', token ? 'present' : 'missing');
    
    // Don't load if no token is available
    if (!token) {
      console.log('CollectionsService: No token available, skipping load');
      return;
    }

    console.log('CollectionsService: Starting to load collections');
    this.isLoadingSignal.set(true);
    this.errorSignal.set(null);

    this.apiService.getCollections().subscribe({
      next: (response) => {
        console.log('CollectionsService: Successfully loaded collections:', response?.collections?.length || 0);
        this.collectionsResponseSignal.set(response);
        this.isLoadingSignal.set(false);
        this.hasLoadedOnceSignal.set(true);
      },
      error: (error) => {
        console.error('CollectionsService: Error loading collections:', error);
        this.errorSignal.set(error.message || 'Failed to load collections');
        this.isLoadingSignal.set(false);
      }
    });
  }

  setFilter(filter: CollectionFilter) {
    this.currentFilterSignal.set(filter);
  }

  createCollection(data: { collection_name: string; is_public: boolean }) {
    return this.apiService.createCollection(data);
  }

  deleteCollection(collectionName: string) {
    return this.apiService.deleteCollections([collectionName]);
  }

  deleteCollections(collectionNames: string[]) {
    return this.apiService.deleteCollections(collectionNames);
  }

  constructor() {
    // Initialize previous token signal with current token
    const initialToken = this.authService.token();
    this.previousTokenSignal.set(initialToken);
    
    // Check if token is already available (e.g., on page refresh)
    if (initialToken && this.authService.status() === 'success') {
      console.log('CollectionsService: Initial token found, loading collections immediately');
      this.loadCollections();
    }

    // Wait for token to be available before loading collections
    // Use effect to reactively load when token becomes available
    effect(() => {
      const token = this.authService.token();
      const status = this.authService.status();
      const previousToken = this.previousTokenSignal();
      
      // If token changed (new login), reset the loaded flag
      if (token !== previousToken) {
        this.previousTokenSignal.set(token);
        if (token) {
          // Token changed and exists - reset loaded flag to allow reload
          this.hasLoadedOnceSignal.set(false);
          this.collectionsResponseSignal.set(null);
        } else {
          // Token removed - clear collections
          this.collectionsResponseSignal.set(null);
          this.hasLoadedOnceSignal.set(false);
        }
      }
      
      // Load if we have a token and status is success
      if (token && status === 'success' && !this.hasLoadedOnceSignal()) {
        console.log('CollectionsService: Token available, loading collections');
        this.loadCollections();
      }
    });
  }
}
