import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withHashLocation, withRouterConfig } from '@angular/router';

import { routes } from './app.routes';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './features/auth/interceptors/auth.interceptor';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { CLIPBOARD_OPTIONS, provideMarkdown } from 'ngx-markdown';
import {
    MarkdownClipboardComponent
} from './features/shared/components/markdown-clipboard/markdown-clipboard.component';


export const appConfig: ApplicationConfig = {
    providers: [
        provideZoneChangeDetection({ eventCoalescing: true }),
        provideAnimations(),
        provideRouter(routes, withHashLocation(), withRouterConfig({ urlUpdateStrategy: 'deferred' })),
        provideHttpClient(
            withInterceptors([authInterceptor])
        ),
        provideAnimationsAsync(),
        provideMarkdown({
            clipboardOptions: {
                provide: CLIPBOARD_OPTIONS,
                useValue: {
                    buttonComponent: MarkdownClipboardComponent,
                }
            }
        }),
    ]
};
