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
  // Stream capture metadata
  camera_id?: string;
  capture_type?: string;
  neighborhood?: string;
  scenario?: string;  // Analysis scenario (surveillance, traffic, egocentric, etc.)
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  tags?: string[];
  include_public?: boolean;
  use_llm?: boolean;
  system_prompt?: string;  // Custom LLM system prompt (overrides backend default)
  time_filter?: string;  // 'all', '5m', '15m', '1h', '24h', '7d', 'custom'
  custom_start_date?: string;  // ISO 8601 format for custom date range
  custom_end_date?: string;    // ISO 8601 format for custom date range
  metadata_filters?: Record<string, any>;  // Dynamic metadata filters
  min_similarity?: number;  // Minimum similarity score threshold (0.1 - 0.8)
  llm_top_n?: number;  // Number of results to send to LLM for analysis
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
  sql_query?: string;
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

export interface MetadataField {
  name: string;
  type: string;
  ui_type: 'text' | 'select' | 'number' | 'checkbox' | 'datetime' | 'tags';
  label: string;
  options?: string[];
}

export interface MetadataSchema {
  schema: MetadataField[];
  table: string;
}

