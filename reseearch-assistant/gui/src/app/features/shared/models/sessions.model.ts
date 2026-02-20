// Session data models and interfaces (aligned with API_DOC.md)

export interface SessionSummary {
  title: string;
  description?: string;
  tags?: string[];
  [key: string]: any; // Allow custom fields
}

export interface SessionMetadata {
  category?: string;
  priority?: string;
  [key: string]: any; // Allow custom fields
}

export interface Session {
  session_id: string;
  created_at: number; // unix timestamp
  updated_at: number; // unix timestamp
  summary: SessionSummary | null;
  metadata: SessionMetadata | null;
}

export interface SessionsResponse {
  sessions: Session[];
  total: number;
}
