export type StreamEventType = 
    | 'start'
    | 'tool_start' 
    | 'tool_complete' 
    | 'tool_end' 
    | 'bedrock_start' 
    | 'bedrock_complete' 
    | 'bedrock_error' 
    | 'content_delta' 
    | 'complete'
    | 'session_id';

export interface ChunkInfo {
    text: string;
    score: number;
    source?: string;
    source_title?: string;
    source_url?: string;
}

export interface CollectionMetadata {
    num_chunks: number;
    num_unique_files: number;
    total_doc_size_bytes: number;
    total_doc_size_mb: number;
}

export interface StreamEvent {
    type: StreamEventType;
    message?: string;
    tool_name?: string;
    arguments?: Record<string, unknown>;
    timestamp?: number;
    duration?: number;
    success?: boolean;
    result?: unknown;
    chunks?: ChunkInfo[];
    citations?: string[];
    collection_metadata?: CollectionMetadata;
    metadata_query_used?: string;
    call_number?: number;
    error?: string;
    delta?: string;
    session_id?: string;
    prompt?: string;
    response?: { content: string };
}

export function formatToolResult(event: StreamEvent): string {
    if ((event.tool_name === 'retrieve_chunks' || event.tool_name === 'hybrid_query') && event.chunks) {
        const chunkSummary = event.chunks
            .slice(0, 3)
            .map(chunk => `- ${chunk.source_title ?? chunk.source ?? 'unknown'}: ${chunk.text.slice(0, 100)}...`)
            .join('\n');
        return `RAG Results: ${event.chunks.length} items\n${chunkSummary}`;
    }
    
    if (event.result) {
        try {
            return '```json\n' + JSON.stringify(event.result, null, 2) + '\n```';
        } catch {
            return String(event.result);
        }
    }
    
    return `Completed in ${event.duration?.toFixed(2) ?? '?'}s`;
}

export function formatDuration(seconds: number): string {
    if (seconds < 1) {
        return `${Math.round(seconds * 1000)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
}

