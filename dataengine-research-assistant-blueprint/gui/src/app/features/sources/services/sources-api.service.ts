import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { SETTINGS } from '../../shared/settings';
import {
  Document,
  SourcesResponse,
  CreateDocumentData,
  UpdateDocumentData,
  UploadDocumentData,
  UploadDocumentResponse
} from '../../shared/models/sources.model';
import { getMockSourcesResponse, createMockDocument, createMockUpdatedDocument } from '../../shared/mocks';

@Injectable({
  providedIn: 'root'
})
export class SourcesApiService {
  private httpClient = inject(HttpClient);

  getSources(collectionName: string): Observable<SourcesResponse> {
    if (SETTINGS.MOCK_MODE) {
      return of(getMockSourcesResponse(collectionName));
    }

    const url = `${SETTINGS.BASE_API_URL}/documents?collection_name=${encodeURIComponent(collectionName)}`;
    return this.httpClient.get<SourcesResponse>(url);
  }

  createDocument(collectionName: string, data: CreateDocumentData): Observable<Document> {
    if (SETTINGS.MOCK_MODE) {
      return of(createMockDocument({
        document_name: data.document_name,
        collection_name: data.collection_name,
        description: data.description,
        tags: data.tags
      }));
    }

    return this.httpClient.post<Document>(`${SETTINGS.BASE_API_URL}/documents`, {
      ...data,
      collection_name: collectionName
    });
  }

  updateDocument(collectionName: string, documentName: string, data: UpdateDocumentData): Observable<Document> {
    if (SETTINGS.MOCK_MODE) {
      return of(createMockUpdatedDocument(data));
    }

    const url = `${SETTINGS.BASE_API_URL}/documents/${encodeURIComponent(documentName)}?collection_name=${encodeURIComponent(collectionName)}`;
    return this.httpClient.patch<Document>(url, data);
  }

  uploadDocument(data: UploadDocumentData): Observable<UploadDocumentResponse> {
    if (SETTINGS.MOCK_MODE) {
      const mockResponse: UploadDocumentResponse = {
        message: 'Ingestion in progress',
        task_id: 'f314de63-ca52-4c32-aa7b-49d803f4a10a' // Mock UUID
      };
      return of(mockResponse);
    }

    const formData = new FormData();
    formData.append('collection_name', data.collection_name);
    formData.append('file', data.file);
    if (data.allowed_groups) {
      formData.append('allowed_groups', data.allowed_groups);
    }
    if (data.is_public !== undefined) {
      formData.append('is_public', data.is_public.toString());
    }

    return this.httpClient.post<UploadDocumentResponse>(`${SETTINGS.BASE_API_URL}/documents`, formData);
  }

  // Note: API doesn't provide DELETE endpoint for documents
  // Keeping for mock purposes only
  deleteDocument(collectionName: string, documentName: string): Observable<void> {
    if (SETTINGS.MOCK_MODE) {
      return of(void 0);
    }

    // This would be a custom endpoint if implemented
    const url = `${SETTINGS.BASE_API_URL}/documents/${encodeURIComponent(documentName)}?collection_name=${encodeURIComponent(collectionName)}`;
    return this.httpClient.delete<void>(url);
  }
}
