import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { SETTINGS } from '../../shared/settings';
import {
  Collection,
  CollectionsResponse,
  FullCollection,
  FullCollectionsResponse,
  CreateCollectionData,
  CreateCollectionResponse,
  DeleteCollectionsResponse
} from '../../shared/models/collections.model';
import { MOCK_COLLECTIONS_RESPONSE, MOCK_FULL_COLLECTIONS_RESPONSE, createMockCollection } from '../../shared/mocks';

@Injectable({
  providedIn: 'root'
})
export class CollectionsApiService {
  private httpClient = inject(HttpClient);

  getCollections(): Observable<CollectionsResponse> {
    if (SETTINGS.MOCK_MODE) {
      return of(MOCK_COLLECTIONS_RESPONSE);
    }

    return this.httpClient.get<CollectionsResponse>(`${SETTINGS.BASE_API_URL}/collections`);
  }

  getFullCollections(collectionName?: string): Observable<FullCollectionsResponse> {
    if (SETTINGS.MOCK_MODE) {
      return of(MOCK_FULL_COLLECTIONS_RESPONSE);
    }

    const url = collectionName
      ? `${SETTINGS.BASE_API_URL}/fullcollections?collection_name=${encodeURIComponent(collectionName)}`
      : `${SETTINGS.BASE_API_URL}/fullcollections`;
    return this.httpClient.get<FullCollectionsResponse>(url);
  }

  createCollection(data: CreateCollectionData): Observable<CreateCollectionResponse> {
    if (SETTINGS.MOCK_MODE) {
      const mockResponse: CreateCollectionResponse = {
        message: 'Collection created successfully',
        collection_name: data.collection_name,
        result: {
          message: 'Created 1 collections successfully',
          successful: [data.collection_name],
          failed: null,
          total_success: 1,
          total_failed: 0
        }
      };
      return of(mockResponse);
    }

    return this.httpClient.post<CreateCollectionResponse>(`${SETTINGS.BASE_API_URL}/collections`, data);
  }

  deleteCollections(collectionNames: string[]): Observable<DeleteCollectionsResponse> {
    if (SETTINGS.MOCK_MODE) {
      const mockResponse: DeleteCollectionsResponse = {
        message: 'Collections deleted successfully',
        deleted_collections: collectionNames
      };
      return of(mockResponse);
    }

    return this.httpClient.delete<DeleteCollectionsResponse>(`${SETTINGS.BASE_API_URL}/collections`, {
      body: collectionNames
    });
  }

}
