// ai-response-stream-http.service.ts
import { Injectable, inject } from '@angular/core';
import {
    HttpClient,
    HttpEvent,
    HttpEventType,
    HttpHeaders
} from '@angular/common/http';
import { filter, from, map, mergeMap, Observable, of, scan } from 'rxjs';
import { environment } from '../../../../environments/environment';
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

/**
 * Сервис, который читает ND-JSON поток через HttpClient.
 * Возвращает Observable<RunResponse>; отписка прервет запрос.
 */
@Injectable({ providedIn: 'root' })
export class AiResponseStreamHttpService {
    private readonly http = inject(HttpClient);
    authService = inject(AuthService);

    bufferM = ''

    streamResponse(
        { apiUrl, headers = {}, requestBody }: StreamOptions
    ) {


        const authToken = this.authService.token();
        //@ts-ignore
        const req$ = this.http.request('POST', apiUrl, {
            body: requestBody instanceof FormData ? requestBody : JSON.stringify(requestBody),
            headers: new HttpHeaders({
                ...(!(requestBody instanceof FormData) && { 'Content-Type': 'application/json' }),
                Authorization: `Bearer ${authToken}`,
                ...headers
            }),
            responseType: 'text',
            observe: 'events',
            reportProgress: true
        });

        // Режем cumulative partialText на «дельты» и превращаем в JSON.
        return req$.pipe(
            filter(
                (e: HttpEvent<string>): e is HttpEvent<string> & { partialText: string } =>
                    e.type === HttpEventType.DownloadProgress && !!(e as any).partialText
            ),
            // превращаем cumulative → delta
            scan(
                (state, e) => {
                    const full = (e as any).partialText;
                    const delta = full.slice(state.prevLen);
                    return { prevLen: full.length, delta };
                },
                { prevLen: 0, delta: '' }
            ),
            map(({ delta }) => {
                let valueArray: any[] = []
                if (this.bufferM) {
                    console.log({
                        b: this.bufferM,
                        val: delta
                    });
                }
                const val = extractJSONObjects(this.bufferM + delta);
                this.bufferM = val.rest;
                valueArray = val.objects;
                return valueArray;
            }),
            mergeMap(value =>
                Array.isArray(value) ? from(value) : of(value)
            )
        );
    }

    parsePartialJSON(input: string) {
        const objects = [];
        const buffer = '';
        let depth = 0;
        let startIndex = null;

        for (let i = 0; i < input.length; i++) {
            const char = input[i];

            if (char === '{') {
                if (depth === 0) {
                    startIndex = i;
                }
                depth++;
            } else if (char === '}') {
                depth--;
                if (depth === 0 && startIndex !== null) {
                    const jsonStr = input.slice(startIndex, i + 1);
                    try {
                        const parsed = JSON.parse(jsonStr);
                        objects.push(parsed);
                        startIndex = null;
                    } catch {

                        return {
                            objects,
                            rest: input.slice(startIndex as number)
                        };
                    }
                }
            }
        }

        const rest = depth > 0 && startIndex !== null ? input.slice(startIndex) : '';
        return { objects, rest };
    }

    private parseBuffer<T>(buf: string, emit: (j: T) => void): string {
        let idx: number;
        while ((idx = buf.indexOf('\n')) !== -1) {
            const line = buf.slice(0, idx).trim();
            buf = buf.slice(idx + 1);
            if (!line) continue;
            try {
                emit(JSON.parse(line));
            } catch {
                // неполный JSON — вернём в буфер и выйдем
                buf = line + '\n' + buf;
                break;
            }
        }
        return buf;
    }
}


function extractJSONObjects(str: any) {
    const objects = [];
    let rest = "";
    let depth = 0;
    let inString = false;
    let escaped = false;
    let startIndex = -1;

    for (let i = 0; i < str.length; i++) {
        const ch = str[i];
        if (!inString) {
            if (depth === 0) {
                // Пока не начали новый JSON, накапливаем всё как остаток
                if (ch === "{" || ch === "[") {
                    // Найден старт JSON-объекта/массива
                    startIndex = i;
                    depth = 1;
                } else {
                    rest += ch;
                }
            } else {
                // Внутри JSON (глубина > 0), вне строки
                if (ch === "{" || ch === "[") {
                    depth++;
                } else if (ch === "}" || ch === "]") {
                    depth--;
                    if (depth === 0) {
                        // Конец JSON-объекта/массива
                        const jsonStr = str.slice(startIndex, i + 1);
                        try {
                            objects.push(JSON.parse(jsonStr));
                        } catch (e) {
                            // Ошибка парсинга (обрезанный или неверный JSON) — всё с места начала до конца считаем остатком
                            rest += str.slice(startIndex);
                            return { objects, rest };
                        }
                        startIndex = -1;
                    }
                } else if (ch === "\"") {
                    // Начало строки внутри JSON
                    inString = true;
                    escaped = false;
                }
                // Прочие символы внутри JSON вне строки обрабатываются в рамках текущего уровня
            }
        } else {
            // Находимся внутри строкового литерала JSON
            if (escaped) {
                // Предыдущий символ был '\', текущий трактуется как экранированный
                escaped = false;
            } else {
                if (ch === "\\") {
                    // Экранирующая последовательность
                    escaped = true;
                } else if (ch === "\"") {
                    // Конец строкового литерала
                    inString = false;
                }
            }
            // Замечание: фигурные скобки внутри строки игнорируются для счётчика глубины
        }
    }

    // Если цикл завершился, а JSON не завершён (не закрыты скобки или кавычки)
    if (depth !== 0 || inString) {
        if (startIndex !== -1) {
            rest += str.slice(startIndex);
        }
    }

    return { objects, rest };
}
