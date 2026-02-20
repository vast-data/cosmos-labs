import {
    afterNextRender,
    ChangeDetectionStrategy,
    Component,
    computed,
    effect,
    ElementRef,
    EnvironmentInjector,
    inject,
    input,
    ViewChild,
    ViewContainerRef
} from '@angular/core';
import MarkdownIt from 'markdown-it';
import mkVideo from 'markdown-it-video';
import { DomSanitizer } from '@angular/platform-browser';
import { markdownBlockHover, sourceListPlugin } from './md-plugins';
import { HoverBlockComponent } from './hover-block/hover-block.component';
import { AnimationCrontrolService } from '../../services/animation-crontrol.service';
import { SourceListComponent } from './source-list/source-list.component';

declare const Prism: {
    highlightAllUnder: (container: Element) => void;
    languages: Record<string, unknown>;
};

@Component({
    selector: 'app-markdown-viewer',
    standalone: true,
    imports: [],
    template: `
        <div #container class="markdown prose max-w-none" [style.opacity]="parsed && !parseAsAngular() ? 0.5 : 1" [innerHTML]="renderedHtml()"></div> `,
    styles: [
        `:host {
            display: block;
        }

        ::ng-deep .code-block-wrapper {
            position: relative;

            .copy-button {
                position: absolute;
                top: 8px;
                right: 8px;
                padding: 4px 8px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                color: #ccc;
                font-size: 12px;
                cursor: pointer;
                opacity: 0;
                transition: opacity 0.2s, background 0.2s;
                z-index: 1;

                &:hover {
                    background: rgba(255, 255, 255, 0.2);
                }

                &.copied {
                    background: rgba(76, 175, 80, 0.3);
                    color: #81c784;
                }
            }

            &:hover .copy-button {
                opacity: 1;
            }

            pre {
                margin: 0;
            }
        }`
    ],
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class MarkdownViewerComponent {
    private md: MarkdownIt;
    private sanitizer: DomSanitizer = inject(DomSanitizer);

    protected parsed = false;

    content = input<string | null>('')
    parseAsAngular = input<boolean | null>(null)
    renderedHtml = computed(() => {
        return this.sanitizer.bypassSecurityTrustHtml(
            this.md.render(this.content() || '')
                .replaceAll('<p>TESTTOWRAPVIDEO</p>', '<div class="video-list">')
                .replaceAll('<p>TESTTOWRAPVIDEO_END</p>', '</div>')
        );
    });

    @ViewChild('container', { static: true }) containerRef!: ElementRef<HTMLElement>

    private viewContainerRef = inject(ViewContainerRef)
    private envInjector = inject(EnvironmentInjector)
    private animation: AnimationCrontrolService = inject(AnimationCrontrolService)

    constructor() {
        this.md = new MarkdownIt({
            html: true,
            linkify: true,
            highlight: (code: string, lang: string): string => {
                const language = lang && Prism.languages[lang] ? lang : 'plaintext';
                const highlighted = this.escapeHtml(code);
                return `<div class="code-block-wrapper"><pre class="language-${language}"><code class="language-${language}">${highlighted}</code></pre></div>`;
            }
        })
            .use(mkVideo)
            .use(markdownBlockHover)
            .use(sourceListPlugin);

        effect(() => {
            if (this.parseAsAngular() === true) {
                console.log('PARSE');
                setTimeout(() => {
                    this.renderMarkdown();
                }, 30);
            }
        });

        afterNextRender(() => {
            this.highlightCode();
        });

        effect(() => {
            // Re-run highlighting when content changes
            this.content();
            setTimeout(() => this.highlightCode(), 0);
        });
    }

    private escapeHtml(code: string): string {
        return code
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    private highlightCode(): void {
        if (this.containerRef?.nativeElement) {
            Prism.highlightAllUnder(this.containerRef.nativeElement);
        }
    }


    renderMarkdown(): void {
        this.parsed = true;
        const html =  this.md.render(this.content() || '')
            .replaceAll('<p>TESTTOWRAPVIDEO</p>', '<div class="video-list">')
            .replaceAll('<p>TESTTOWRAPVIDEO_END</p>', '</div>')
        this.containerRef.nativeElement.innerHTML = html

        const rawBlocks = Array.from(this.containerRef.nativeElement.querySelectorAll('app-hover-block'))

        for (const rawEl of rawBlocks) {
            const wrapper = document.createElement('div')
            rawEl.replaceWith(wrapper)

            const compRef = this.viewContainerRef.createComponent(HoverBlockComponent, {
                environmentInjector: this.envInjector,
            })

            const content = Array.from(rawEl.childNodes)
            for (const node of content) {
                compRef.location.nativeElement.appendChild(node)
            }

            for (const attr of Array.from(rawEl.attributes)) {
                compRef.setInput(attr.name, attr.value);
            }

            wrapper.replaceWith(compRef.location.nativeElement)
        }


        const rawSourcesBlocks = Array.from(this.containerRef.nativeElement.querySelectorAll('app-source-list'))

        for (const rawEl of rawSourcesBlocks) {
            const wrapper = document.createElement('div')
            rawEl.replaceWith(wrapper)

            const compRef = this.viewContainerRef.createComponent(SourceListComponent, {
                environmentInjector: this.envInjector,
            })

            const content = Array.from(rawEl.childNodes)
            for (const node of content) {
                compRef.location.nativeElement.appendChild(node)
            }

            for (const attr of Array.from(rawEl.attributes)) {
                compRef.setInput(attr.name, attr.value);
            }

            wrapper.replaceWith(compRef.location.nativeElement);
        }

        this.highlightCode();
    }
}
