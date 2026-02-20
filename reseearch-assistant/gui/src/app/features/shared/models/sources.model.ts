// Sources/Documents data models and interfaces (aligned with API_DOC.md)

export interface Document {
  document_name: string;
  collection_name?: string;
  description?: string;
  tags: string[];
}

// Note: API doesn't provide GET endpoint for listing documents per collection
// Documents can only be uploaded via POST /documents
// For now, we'll keep mock data for development purposes

export interface UploadDocumentData {
  collection_name: string;
  file: File;
  allowed_groups?: string; // comma-separated
  is_public?: boolean;
}

export interface UploadDocumentResponse {
  message: string;
  task_id: string; // UUID
}

export interface SourcesResponse {
  message: string;
  total_documents: string;
  documents: Document[];
}

export interface CreateDocumentData {
  document_name: string;
  collection_name?: string;
  description?: string;
  tags?: string[];
}

export interface UpdateDocumentData {
  document_name: string;
  collection_name: string;
  description?: string;
  tags: string[];
}

export interface SourceFilter {
  searchTerm?: string;
}
