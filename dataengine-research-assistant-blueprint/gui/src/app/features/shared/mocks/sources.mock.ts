import { SourcesResponse, Document } from '../models/sources.model';

// Mock sources data for development
export function getMockSourcesResponse(collectionName: string): SourcesResponse {
  return {
    message: 'Documents retrieved successfully',
    total_documents: '5',
    documents: [
      {
        document_name: 'user-manual.pdf',
        collection_name: collectionName,
        description: 'Comprehensive user manual for the application',
        tags: ['documentation', 'user-guide']
      },
      {
        document_name: 'technical-specification.docx',
        collection_name: collectionName,
        description: 'Technical specifications and architecture details',
        tags: ['technical', 'specifications']
      },
      {
        document_name: 'project-overview.md',
        collection_name: collectionName,
        description: 'High-level project overview and goals',
        tags: ['overview', 'project']
      },
      {
        document_name: 'api-documentation.json',
        collection_name: collectionName,
        description: 'API documentation and endpoints',
        tags: ['api', 'documentation']
      },
      {
        document_name: 'meeting-notes.txt',
        collection_name: collectionName,
        description: 'Meeting notes and action items',
        tags: ['meetings', 'notes']
      }
    ]
  };
}

export function createMockDocument(data: {
  document_name: string;
  collection_name?: string;
  description?: string;
  tags?: string[];
}): Document {
  return {
    document_name: data.document_name,
    collection_name: data.collection_name,
    description: data.description,
    tags: data.tags || []
  };
}

export function createMockUpdatedDocument(data: {
  document_name: string;
  collection_name: string;
  description?: string;
  tags: string[];
}): Document {
  return {
    document_name: data.document_name,
    collection_name: data.collection_name,
    description: data.description,
    tags: data.tags
  };
}
