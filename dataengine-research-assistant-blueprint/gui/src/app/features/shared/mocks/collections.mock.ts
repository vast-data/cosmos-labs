import { CollectionsResponse, FullCollectionsResponse, Collection, FullCollection, CreateCollectionResponse } from '../models/collections.model';

function getCollectionTitle(collectionId: string): string {
  const parts = collectionId.split('__');
  return parts.length > 1 ? parts[1] : collectionId;
}

function isCollectionPrivate(collectionId: string): boolean {
  return collectionId.includes('__');
}

// Mock collections data for development (aligned with API_DOC.md)
export const MOCK_COLLECTIONS_RESPONSE: CollectionsResponse = {
  collections: [
    {
      id: 'yuval6__test_collection_api_001',
      description: '1 files | source: api | users: yuval6',
      title: 'test_collection_api_001',
      private: true
    },
    {
      id: 'yuval6__example_collection_4',
      description: '0 files | source: api | users: yuval6',
      title: 'example_collection_4',
      private: true
    },
    {
      id: 'yuval6__democollection2',
      description: '0 files | source: api | users: yuval6',
      title: 'democollection2',
      private: true
    },
    {
      id: 'yuval6__democollection1',
      description: '1 files | source: api | users: yuval6',
      title: 'democollection1',
      private: true
    },
    {
      id: 'yuval6__vast_documents',
      description: '1 files | source: api | users: yuval6',
      title: 'vast_documents',
      private: true
    },
    {
      id: 'yuval6__example_collection_5',
      description: '0 files | source: api | users: yuval6',
      title: 'example_collection_5',
      private: true
    },
    {
      id: 'yuval6__example_collection_2',
      description: '0 files | source: api | users: yuval6',
      title: 'example_collection_2',
      private: true
    },
    {
      id: 'yuval6__example_collection_3',
      description: '0 files | source: api | users: yuval6',
      title: 'example_collection_3',
      private: true
    },
    {
      id: 'yuval6__example_collection_1',
      description: '0 files | source: api | users: yuval6',
      title: 'example_collection_1',
      private: true
    },
    {
      id: 'yuval6__test_collection_api_docs',
      description: '0 files | source: api | users: yuval6',
      title: 'test_collection_api_docs',
      private: true
    }
  ]
};

export const MOCK_FULL_COLLECTIONS_RESPONSE: FullCollectionsResponse = {
  collections: [
    {
      name: 'yuval6__vast_documents',
      num_chunks: 1523,
      num_unique_files: 45,
      total_doc_size_bytes: 15728640,
      total_doc_size_mb: 15.0
    },
    {
      name: 'yuval6__test_collection',
      num_chunks: 234,
      num_unique_files: 12,
      total_doc_size_bytes: 5242880,
      total_doc_size_mb: 5.0
    }
  ],
  total: 2
};

export function createMockCollection(data: { collection_name: string; tags?: string[] }): Collection {
  return {
    id: data.collection_name,
    description: '0 files | source: api | users: yuval6',
    title: getCollectionTitle(data.collection_name),
    private: isCollectionPrivate(data.collection_name)
  };
}

export function createMockCreateCollectionResponse(data: { collection_name: string }): CreateCollectionResponse {
  return {
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
}
