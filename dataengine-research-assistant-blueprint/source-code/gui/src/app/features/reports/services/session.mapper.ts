export interface ToolStartEvent {
    type: 'tool_start';
    tool_name: string;
    arguments: Record<string, unknown>;
    timestamp: number;
}

export interface ToolEndedEvent {
    type: 'tool_ended';
    tool_name: string;
    duration: number;
    success: boolean;
    timestamp: number;
    citations?: string[];
    chunks?: ApiRetrievedChunk[];
    collection_metadata?: ApiCollectionMetadata;
    metadata_query_used?: string;
}

export type ApiToolEvent = ToolStartEvent | ToolEndedEvent;

export interface ApiRetrievedChunk {
    text: string;
    score: number;
    source?: string;
    source_title?: string;
    source_url?: string;
}

export interface ApiCollectionMetadata {
    num_chunks: number;
    num_unique_files: number;
    total_doc_size_bytes: number;
    total_doc_size_mb: number;
}

export interface ApiMessage {
    role: 'system' | 'user' | 'assistant';
    content: string | unknown[];
    created_at: number;
    citations?: string[] | null;
    collection_metadata?: ApiCollectionMetadata | null;
    tool_events?: ApiToolEvent[];
}

export interface SessionResponse {
    session_id: string;
    created_at: number;
    updated_at: number;
    summary: { title?: string } | null;
    metadata: Record<string, unknown> | null;
    messages: ApiMessage[] | null;
    citations?: string[] | null;
}

// Content block types for AI message content array
export type MessageContentBlock = TextContentBlock | ToolContentBlock | LoadingContentBlock;

export interface TextContentBlock {
    type: 'text';
    text: string;
}

export interface LoadingContentBlock {
    type: 'loading';
    message?: string;
}

export interface RetrievedChunk {
    text: string;
    score: number;
    source?: string;
    sourceTitle?: string;
    sourceUrl?: string;
}

export interface CollectionMetadata {
    num_chunks: number;
    num_unique_files: number;
    total_doc_size_bytes: number;
    total_doc_size_mb: number;
}

export interface ToolContentBlock {
    type: 'tool';
    toolName: string;
    status: 'loading' | 'success' | 'error' | 'warning';
    prompt?: string;
    startTimestamp?: number;
    duration?: number;
    arguments?: Record<string, unknown>;
    citations?: string[];
    chunks?: RetrievedChunk[];
    collectionMetadata?: CollectionMetadata;
    metadataQueryUsed?: string;
    error?: string;
}

export interface ChatMessage {
    content: string | MessageContentBlock[];
    role: 'human' | 'ai' | 'report';
    type?: 'plan' | 'streamResponse';
    sources?: unknown[];
    hide?: boolean;
    isPlan?: boolean;
    thinking?: boolean;
    steps?: ToolStep[];
    status?: string;
    citations?: string[];
    animate?: boolean;
}

export interface ToolStep {
    title: string;
    description: string;
    content?: string;
    status: 'loading' | 'success' | 'error';
    toRemove?: boolean;
}

export function mapApiMessagesToChatHistory(messages: ApiMessage[] | null): ChatMessage[] {
    if (!messages) return [];

    const filteredMessages = messages
        .filter(msg => msg.role !== 'system' && !Array.isArray(msg.content));

    const result: ChatMessage[] = [];
    let pendingAssistantMessages: ApiMessage[] = [];

    for (const msg of filteredMessages) {
        if (msg.role === 'user') {
            if (pendingAssistantMessages.length > 0) {
                result.push(mergeAssistantMessages(pendingAssistantMessages));
                pendingAssistantMessages = [];
            }
            result.push(mapUserMessage(msg));
        } else if (msg.role === 'assistant') {
            pendingAssistantMessages.push(msg);
        }
    }

    if (pendingAssistantMessages.length > 0) {
        result.push(mergeAssistantMessages(pendingAssistantMessages));
    }

    return result;
}

function mapUserMessage(msg: ApiMessage): ChatMessage {
    const content = typeof msg.content === 'string' ? msg.content : '';
    return {
        content,
        role: 'human',
        sources: [],
        animate: false
    };
}

function mergeAssistantMessages(messages: ApiMessage[]): ChatMessage {
    const contentBlocks: MessageContentBlock[] = [];
    const allCitations: string[] = [];

    for (const msg of messages) {
        if (typeof msg.content === 'string' && msg.content) {
            contentBlocks.push({ type: 'text', text: msg.content });
        }

        if (msg.tool_events?.length) {
            const toolBlocks = mapToolEventsToContentBlocks(msg.tool_events);
            contentBlocks.push(...toolBlocks);
        }

        if (msg.citations?.length) {
            allCitations.push(...msg.citations);
        }
    }

    if (contentBlocks.length === 0) {
        contentBlocks.push({ type: 'text', text: '' });
    }

    return {
        content: contentBlocks,
        role: 'ai',
        sources: [],
        citations: allCitations.length > 0 ? allCitations : undefined,
        animate: false
    };
}

function mapToolEventsToContentBlocks(toolEvents: ApiToolEvent[]): MessageContentBlock[] {
    const contentBlocks: MessageContentBlock[] = [];
    const pendingTools = new Map<string, ToolStartEvent>();

    for (const event of toolEvents) {
        if (event.type === 'tool_start') {
            pendingTools.set(event.tool_name, event);
        } else if (event.type === 'tool_ended') {
            const startEvent = pendingTools.get(event.tool_name);
            
            const toolBlock: MessageContentBlock = {
                type: 'tool',
                toolName: event.tool_name,
                status: event.success ? 'success' : 'error',
                startTimestamp: startEvent?.timestamp,
                duration: event.duration,
                arguments: startEvent?.arguments,
                citations: event.citations,
                chunks: event.chunks?.map(chunk => ({
                    text: chunk.text,
                    score: chunk.score,
                    source: chunk.source,
                    sourceTitle: chunk.source_title,
                    sourceUrl: chunk.source_url
                })),
                collectionMetadata: event.collection_metadata || undefined,
                metadataQueryUsed: event.metadata_query_used || undefined
            };

            contentBlocks.push(toolBlock);
            pendingTools.delete(event.tool_name);
        }
    }

    return contentBlocks;
}
