export interface VideoSearchResult {
  filename: string;
  source: string;
  reasoning_content: string;
  video_url: string;
  is_public: boolean;
  upload_timestamp: string;
  duration: number;
  segment_number: number;
  total_segments: number;
  original_video: string;
  tags: string[];
  similarity_score: number;
  cosmos_model?: string;
  tokens_used?: number;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  tags?: string[];
  include_public?: boolean;
  use_llm?: boolean;
}

export interface LLMSynthesis {
  response: string;
  segments_used: number;
  segments_analyzed: string[];
  model: string;
  tokens_used: number;
  processing_time: number;
  error?: string | null;
}

export interface SearchResponse {
  results: VideoSearchResult[];
  total: number;
  query: string;
  embedding_time_ms: number;
  search_time_ms: number;
  permission_filtered: number;
  llm_synthesis?: LLMSynthesis | null;
}

export interface UploadRequest {
  is_public: boolean;
  tags: string[];
  allowed_users: string[];
}

export interface UploadResponse {
  upload_url: string;
  object_key: string;
  expires_in: number;
  fields: Record<string, string>;  // Presigned POST fields (for S3 upload)
  metadata: Record<string, any>;   // Metadata for display only
}

