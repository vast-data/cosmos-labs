import { Injectable, inject, NgZone } from '@angular/core';
import { Observable, Subscriber } from 'rxjs';
import { AuthService } from '../../auth/services/auth.service';

export interface RunResponse {
    id: string;
    content: unknown;
}

export interface StreamOptions {
    apiUrl: string;
    headers?: Record<string, string>;
    requestBody: FormData | Record<string, unknown>;
}

const CONTENT_FLUSH_INTERVAL_MS = 50;

/**
 * Streaming service using fetch() + ReadableStream for real-time token delivery.
 *
 * content_delta events are batched into ~50ms windows so the UI updates at
 * ~20 fps instead of triggering a change-detection cycle per token.
 * All other event types (tool_start, tool_complete, complete, etc.) are
 * emitted immediately.
 */
@Injectable({ providedIn: 'root' })
export class AiResponseStreamHttpService {
    private readonly authService = inject(AuthService);
    private readonly ngZone = inject(NgZone);

    streamResponse({ apiUrl, headers = {}, requestBody }: StreamOptions): Observable<any> {
        return new Observable((subscriber: Subscriber<any>) => {
            const abortController = new AbortController();

            const authToken = this.authService.token();
            const isFormData = requestBody instanceof FormData;

            const fetchHeaders: Record<string, string> = {
                Authorization: `Bearer ${authToken}`,
                ...headers
            };
            if (!isFormData) {
                fetchHeaders['Content-Type'] = 'application/json';
            }

            const body = isFormData ? requestBody : JSON.stringify(requestBody);

            const ctx = this.createFlushContext(subscriber);
            this.readStream(apiUrl, fetchHeaders, body, abortController, subscriber, ctx);

            return () => {
                abortController.abort();
                this.clearFlushContext(ctx);
            };
        });
    }

    // ── content_delta batching ──────────────────────────────────────────

    private createFlushContext(subscriber: Subscriber<any>): FlushContext {
        return { pendingDelta: '', timerId: null, subscriber };
    }

    private clearFlushContext(ctx: FlushContext): void {
        if (ctx.timerId !== null) {
            clearTimeout(ctx.timerId);
            ctx.timerId = null;
        }
    }

    private appendDelta(ctx: FlushContext, delta: string): void {
        ctx.pendingDelta += delta;
        if (ctx.timerId === null) {
            ctx.timerId = window.setTimeout(() => this.flushDelta(ctx), CONTENT_FLUSH_INTERVAL_MS);
        }
    }

    private flushDelta(ctx: FlushContext): void {
        ctx.timerId = null;
        if (!ctx.pendingDelta || ctx.subscriber.closed) return;
        const combined = ctx.pendingDelta;
        ctx.pendingDelta = '';
        this.ngZone.run(() => {
            if (!ctx.subscriber.closed) {
                ctx.subscriber.next({ type: 'content_delta', delta: combined });
            }
        });
    }

    // ── stream reader ──────────────────────────────────────────────────

    private async readStream(
        url: string,
        headers: Record<string, string>,
        body: BodyInit,
        abortController: AbortController,
        subscriber: Subscriber<any>,
        ctx: FlushContext
    ): Promise<void> {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers,
                body,
                signal: abortController.signal
            });

            if (!response.ok) {
                this.emitInZone(subscriber, 'error', new Error(`HTTP ${response.status}: ${response.statusText}`));
                return;
            }

            const reader = response.body?.getReader();
            if (!reader) {
                this.emitInZone(subscriber, 'error', new Error('Response body is not readable'));
                return;
            }

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                const { objects, rest } = extractJSONObjects(buffer);
                buffer = rest;

                for (const obj of objects) {
                    if (obj?.type === 'content_delta' && typeof obj.delta === 'string') {
                        this.appendDelta(ctx, obj.delta);
                    } else {
                        // Flush any pending content before emitting a non-content event
                        // so ordering is preserved (e.g. complete after last delta).
                        this.flushDelta(ctx);
                        this.emitInZone(subscriber, 'next', obj);
                    }
                }
            }

            // Process any remaining buffer
            if (buffer.trim()) {
                const { objects } = extractJSONObjects(buffer);
                for (const obj of objects) {
                    if (obj?.type === 'content_delta' && typeof obj.delta === 'string') {
                        this.appendDelta(ctx, obj.delta);
                    } else {
                        this.flushDelta(ctx);
                        this.emitInZone(subscriber, 'next', obj);
                    }
                }
            }

            // Flush any remaining content deltas before completing
            this.flushDelta(ctx);
            this.emitInZone(subscriber, 'complete');
        } catch (err: any) {
            this.clearFlushContext(ctx);
            if (err?.name === 'AbortError') {
                this.emitInZone(subscriber, 'complete');
            } else {
                this.emitInZone(subscriber, 'error', err);
            }
        }
    }

    private emitInZone(subscriber: Subscriber<any>, type: 'next' | 'error' | 'complete', value?: any): void {
        this.ngZone.run(() => {
            if (subscriber.closed) return;
            switch (type) {
                case 'next':
                    subscriber.next(value);
                    break;
                case 'error':
                    subscriber.error(value);
                    break;
                case 'complete':
                    subscriber.complete();
                    break;
            }
        });
    }
}

interface FlushContext {
    pendingDelta: string;
    timerId: ReturnType<typeof setTimeout> | null;
    subscriber: Subscriber<any>;
}


function extractJSONObjects(str: string): { objects: any[]; rest: string } {
    const objects: any[] = [];
    let rest = '';
    let depth = 0;
    let inString = false;
    let escaped = false;
    let startIndex = -1;

    for (let i = 0; i < str.length; i++) {
        const ch = str[i];
        if (!inString) {
            if (depth === 0) {
                if (ch === '{' || ch === '[') {
                    startIndex = i;
                    depth = 1;
                } else {
                    rest += ch;
                }
            } else {
                if (ch === '{' || ch === '[') {
                    depth++;
                } else if (ch === '}' || ch === ']') {
                    depth--;
                    if (depth === 0) {
                        const jsonStr = str.slice(startIndex, i + 1);
                        try {
                            objects.push(JSON.parse(jsonStr));
                        } catch {
                            rest += str.slice(startIndex);
                            return { objects, rest };
                        }
                        startIndex = -1;
                    }
                } else if (ch === '"') {
                    inString = true;
                    escaped = false;
                }
            }
        } else {
            if (escaped) {
                escaped = false;
            } else {
                if (ch === '\\') {
                    escaped = true;
                } else if (ch === '"') {
                    inString = false;
                }
            }
        }
    }

    if ((depth !== 0 || inString) && startIndex !== -1) {
        rest += str.slice(startIndex);
    }

    return { objects, rest };
}
