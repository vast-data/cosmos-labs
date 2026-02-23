import { computed, effect, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, of } from 'rxjs';

import { SETTINGS } from '../../shared/settings';
import { AiResponseStreamHttpService } from './ai-response-stream.service';
import { ReportApiService } from './report-api.service';
import {
    ChatMessage,
    mapApiMessagesToChatHistory,
    MessageContentBlock,
    TextContentBlock,
    ToolContentBlock,
    LoadingContentBlock
} from './session.mapper';
import { StreamEvent } from '../utils/stream-event.utils';
import { Collection } from '../../shared/models/collections.model';

interface Conversation {
    id: number;
    title?: string;
    lastMessage?: string;
    createdAt?: Date;
}

interface ReportState {
    isNew: boolean;
    isPlan: boolean;
    conversationsList: Conversation[];
    selectedChat: string | null;
    report: string;
    chatHistory: ChatMessage[];
    promptStatus: 'pending' | 'loading' | 'success' | 'error' | 'responding';
    historyStatus: 'idle' | 'loading' | 'success' | 'error';
    openedHistory: boolean;
}

@Injectable()
export class ReportPageStoreService {
    private readonly router = inject(Router);
    private readonly reportApiService = inject(ReportApiService);
    private readonly aiResponseStreamHttpService = inject(AiResponseStreamHttpService);

    public responding = signal(false);

    protected state = signal<ReportState>({
        isNew: true,
        isPlan: false,
        conversationsList: [],
        selectedChat: null,
        report: '',
        chatHistory: [],
        promptStatus: 'pending',
        historyStatus: 'idle',
        openedHistory: !!localStorage.getItem(SETTINGS.IS_SIDE_MEUN_OPENED_KEY)
    });

    conversations = computed(() => this.state().conversationsList);
    selectedChat = computed(() => this.state().selectedChat);
    chatHistory = computed(() => this.state().chatHistory);
    chatHistoryForSide = computed(() => this.state().chatHistory.filter((item: ChatMessage) => item.type !== 'plan'));
    openedHistory = computed(() => this.state().openedHistory);
    promptStatus = computed(() => this.state().promptStatus);
    historyStatus = computed(() => this.state().historyStatus);
    report = computed(() => this.state().report);
    isNew = computed(() => this.state().isNew);
    standaloneChat = computed(() => true);
    isReadyToProceed = computed(() => this.state().isPlan);

    loadSessionHistory(chatId: string): void {
        console.log(chatId, this.state().selectedChat);
        
        if (chatId === this.state().selectedChat) {
            return;
        }

        if (!chatId || chatId === 'new') {
            this.updateState({
                selectedChat: chatId === 'new' ? null : chatId,
                chatHistory: [],
                historyStatus: 'idle',
                isNew: true
            });
            return;
        }

        this.updateState({
            selectedChat: chatId,
            historyStatus: 'loading',
            chatHistory: [],
            isNew: false
        });

        this.reportApiService.getSession(chatId)
            .pipe(
                catchError(error => {
                    console.error('Failed to load session history:', error);
                    this.updateState({ historyStatus: 'error' });
                    return of(null);
                })
            )
            .subscribe(response => {
                if (!response) return;

                const chatHistory = mapApiMessagesToChatHistory(response.messages);
                this.updateState({
                    chatHistory,
                    historyStatus: 'success',
                    isNew: chatHistory.length === 0
                });
            });
    }

    private updateState(updates: Partial<ReportState>): void {
        this.state.update(state => ({ ...state, ...updates }));
    }

    private addChatMessage(message: ChatMessage): void {
        this.state.update(state => ({
            ...state,
            chatHistory: [...state.chatHistory, message]
        }));
    }

    private updateLastChatMessage(updates: Partial<ChatMessage>): void {
        this.state.update(state => {
            const history = [...state.chatHistory];
            const lastIndex = history.length - 1;
            if (lastIndex >= 0) {
                history[lastIndex] = { ...history[lastIndex], ...updates };
            }
            return { ...state, chatHistory: history };
        });
    }

    private replaceLastChatMessage(message: ChatMessage): void {
        this.state.update(state => ({
            ...state,
            chatHistory: [...state.chatHistory.slice(0, -1), message]
        }));
    }

    constructor() {
        console.log('ReportPageStoreService constructor');

        effect(() => {
            console.log('state', this.selectedChat());
        });
    }

    setSelectedChat(id: string | null, isNew = false, emptyUrl = 'new'): void {
        console.log('setSelectedChat', id, isNew, emptyUrl);
        
        this.updateState({ selectedChat: id, promptStatus: 'pending', isNew: isNew });
        
        console.log(this.state().selectedChat);
        
        if (id === null) {
            this.router.navigate(['chat', emptyUrl]);
            this.updateState({ chatHistory: [] });
        } else {
            this.router.navigate(['chat', id]);
            if (!isNew) {
                this.loadSessionHistory(id);
            }
        }
    }

    sendMessage(prompt: { message: string, deepThinking: boolean, internetSearch: boolean, collection: Collection | null, systemPrompt?: string | null }, hideForUser = false): void {
        this.addChatMessage({
            content: prompt.message,
            role: 'human',
            sources: [],
            hide: hideForUser
        });
        
        this.updateState({ isNew: false, promptStatus: 'responding' });
        this.processPromptStream(prompt.message, prompt.deepThinking, prompt.internetSearch, prompt.collection, prompt.systemPrompt);
    }

    private processPromptStream(prompt: string, deepThinking: boolean, internetSearch: boolean, collection: Collection | null, systemPrompt?: string | null): void {
        this.updateState({ promptStatus: 'loading' });
        this.responding.set(true);

        const selectedChat = this.state().selectedChat;
        const requestBody: Record<string, unknown> = {
            prompt,
            ...(selectedChat ? { conversation_id: selectedChat } : {}),
            ...(collection ? { collections: [collection.id] } : {}),
            ...(deepThinking ? { tools: ['think'] } : {}),
            ...(internetSearch ? { internet_search: true } : {}),
            ...(systemPrompt ? { system_prompt: systemPrompt } : {})
        };

        this.aiResponseStreamHttpService.streamResponse({
            apiUrl: `${SETTINGS.BASE_API_URL}/prompt/stream`,
            requestBody
        }).subscribe({
            next: (event: StreamEvent) => this.handleStreamEvent(event),
            error: () => this.handleStreamError(),
            complete: () => this.handleStreamComplete()
        });
    }

    private handleStreamEvent(event: StreamEvent): void {
        switch (event.type) {
            case 'tool_start':
                this.handleToolStartEvent(event);
                break;
            case 'tool_complete':
            case 'tool_end':
                this.handleToolCompleteEvent(event);
                break;
            case 'bedrock_error':
                console.error('Bedrock API error:', event.error);
                break;
            case 'content_delta':
                this.handleContentDelta(event);
                break;
            case 'complete':
                this.handleCompleteEvent(event);
                break;
        }
    }

    private handleToolStartEvent(event: StreamEvent): void {
        const lastMessage = this.getLastMessage();
        const toolBlock: ToolContentBlock = {
            type: 'tool',
            toolName: event.tool_name ?? 'Processing',
            status: 'loading',
            startTimestamp: event.timestamp,
            arguments: event.arguments
        };

        if (lastMessage?.type === 'streamResponse' && Array.isArray(lastMessage.content)) {
            const filteredContent = this.removeLoadingBlocks(lastMessage.content);
            const updatedContent: MessageContentBlock[] = [...filteredContent, toolBlock];
            this.updateLastChatMessage({ content: updatedContent });
        } else {
            this.addChatMessage({
                content: [toolBlock],
                role: 'ai',
                type: 'streamResponse',
                sources: [],
                animate: true
            });
        }
    }

    private handleToolCompleteEvent(event: StreamEvent): void {
        const lastMessage = this.getLastMessage();
        if (!lastMessage || !Array.isArray(lastMessage.content)) return;

        const updatedContent = [...lastMessage.content] as MessageContentBlock[];
        
        // Find the last tool block with loading status
        for (let i = updatedContent.length - 1; i >= 0; i--) {
            const block = updatedContent[i];
            if (block.type === 'tool' && block.status === 'loading') {
                // Check if error is "No results found" - treat as warning instead of error
                const isNoResults = event.error === 'No results found';
                let status: 'success' | 'error' | 'warning';
                if (event.success) {
                    status = 'success';
                } else if (isNoResults) {
                    status = 'warning';
                } else {
                    status = 'error';
                }

                updatedContent[i] = {
                    ...block,
                    status,
                    duration: event.duration,
                    citations: event.citations,
                    chunks: event.chunks?.map(chunk => ({
                        text: chunk.text,
                        score: chunk.score,
                        source: chunk.source,
                        sourceTitle: chunk.source_title,
                        sourceUrl: chunk.source_url
                    })),
                    prompt: event.prompt,
                    collectionMetadata: event.collection_metadata ? {
                        num_chunks: event.collection_metadata.num_chunks,
                        num_unique_files: event.collection_metadata.num_unique_files,
                        total_doc_size_bytes: event.collection_metadata.total_doc_size_bytes,
                        total_doc_size_mb: event.collection_metadata.total_doc_size_mb
                    } : undefined,
                    metadataQueryUsed: event.metadata_query_used || undefined,
                    error: isNoResults ? 'No results found' : event.error
                };
                break;
            }
        }

        // Add loading indicator after tool completes
        const loadingBlock: LoadingContentBlock = { type: 'loading', message: 'Processing results...' };
        updatedContent.push(loadingBlock);

        this.updateLastChatMessage({ content: updatedContent });
    }

    private handleContentDelta(event: StreamEvent): void {
        const delta = event.delta ?? '';
        if (!delta) return;

        const lastMessage = this.getLastMessage();
        
        if (lastMessage?.type === 'streamResponse' && Array.isArray(lastMessage.content)) {
            // Remove any loading blocks first
            let updatedContent = this.removeLoadingBlocks(lastMessage.content);
            const lastBlock = updatedContent[updatedContent.length - 1];
            
            if (lastBlock?.type === 'text') {
                // Append to existing text block
                updatedContent[updatedContent.length - 1] = {
                    ...lastBlock,
                    text: lastBlock.text + delta
                };
                this.updateLastChatMessage({ content: updatedContent });
            } else {
                // Add new text block
                const newTextBlock: TextContentBlock = { type: 'text', text: delta };
                updatedContent = [...updatedContent, newTextBlock];
                this.updateLastChatMessage({ content: updatedContent });
            }
        } else {
            // Create new message with text block
            const textBlock: TextContentBlock = { type: 'text', text: delta };
            this.addChatMessage({
                content: [textBlock],
                role: 'ai',
                type: 'streamResponse',
                sources: [],
                animate: true
            });
        }

        this.updateState({ promptStatus: 'responding' });
    }

    private removeLoadingBlocks(content: MessageContentBlock[]): MessageContentBlock[] {
        return content.filter(block => block.type !== 'loading');
    }

    private handleCompleteEvent(event: StreamEvent): void {
        if (event.session_id && !this.state().selectedChat) {
            // this.setSelectedChat(event.session_id, true);
            this.updateState({ selectedChat: event.session_id });
        }

        const lastMessage = this.getLastMessage();
        if (lastMessage?.type === 'streamResponse' && Array.isArray(lastMessage.content)) {
            // Remove any remaining loading blocks and mark as complete
            const filteredContent = this.removeLoadingBlocks(lastMessage.content);
            this.updateLastChatMessage({
                content: filteredContent,
                type: undefined,
                animate: false
            });
        }

        this.updateState({ promptStatus: 'success' });
    }

    private handleStreamError(): void {
        this.updateState({ promptStatus: 'error' });
        this.responding.set(false);
    }

    private handleStreamComplete(): void {
        this.responding.set(false);
    }

    private getLastMessage(): ChatMessage | undefined {
        const history = this.state().chatHistory;
        return history[history.length - 1];
    }
}
