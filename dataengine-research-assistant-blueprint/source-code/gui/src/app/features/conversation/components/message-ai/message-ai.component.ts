import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    Output,
    AfterViewInit,
    inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { StringToFlowPipe } from '../../../shared/pipes/string-to-flow.pipe';
import { MarkdownViewerComponent } from '../../../shared/components/markdown-viewer/markdown-viewer.component';
import { ToolBlockComponent } from '../tool-block/tool-block.component';
import { PdfExportService } from '../../../shared/services/pdf-export.service';
import {
    ChatMessage,
    MessageContentBlock,
    TextContentBlock,
    ToolContentBlock,
    LoadingContentBlock
} from '../../../reports/services/session.mapper';

@Component({
    selector: 'app-message-ai',
    standalone: true,
    imports: [
        CommonModule,
        StringToFlowPipe,
        MarkdownViewerComponent,
        ToolBlockComponent,
        MatIconModule,
        MatButtonModule,
        MatMenuModule,
        MatTooltipModule,
        MatSnackBarModule
    ],
    templateUrl: './message-ai.component.html',
    styleUrl: './message-ai.component.scss',
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class MessageAiComponent implements AfterViewInit {
    private pdfService = inject(PdfExportService);
    private snackBar = inject(MatSnackBar);

    private _animate = false;

    @Input() set animate(val: boolean) {
        if (!this._animate) this._animate = val;
    }
    get animate() { return this._animate; }

    @Input() message: ChatMessage | null = null;
    @Input() userPrompt: string = '';
    @Input() showLoading = false;

    @Output() afterAnimation = new EventEmitter<void>();

    loadingBars = new Array<void>(3);

    get contentBlocks(): MessageContentBlock[] {
        if (!this.message) return [];

        if (typeof this.message.content === 'string') {
            return [{ type: 'text', text: this.message.content }];
        }

        return this.message.content ?? [];
    }

    isTextBlock(block: MessageContentBlock): block is TextContentBlock {
        return block.type === 'text';
    }

    isToolBlock(block: MessageContentBlock): block is ToolContentBlock {
        return block.type === 'tool';
    }

    isLoadingBlock(block: MessageContentBlock): block is LoadingContentBlock {
        return block.type === 'loading';
    }

    getTextContent(block: MessageContentBlock): string {
        return this.isTextBlock(block) ? block.text : '';
    }

    getToolBlock(block: MessageContentBlock): ToolContentBlock {
        return block as ToolContentBlock;
    }

    getLoadingMessage(block: MessageContentBlock): string {
        return this.isLoadingBlock(block) ? (block.message ?? 'Processing...') : '';
    }

    trackByIndex(index: number): number {
        return index;
    }

    ngAfterViewInit() {
        if (this.animate) {
            setTimeout(() => { this.afterAnimation.emit(); }, 5000);
        }
    }

    copyToClipboard(): void {
        if (!this.message) return;
        const response = this.pdfService.extractPlainText(this.message);
        const text = this.userPrompt
            ? `Q: ${this.userPrompt}\n\n${response}`
            : response;
        navigator.clipboard.writeText(text).then(() => {
            this.snackBar.open('Copied to clipboard', '', { duration: 2000, horizontalPosition: 'center', verticalPosition: 'bottom' });
        });
    }

    exportToPdf(): void {
        if (!this.message) return;
        const messages: ChatMessage[] = [];
        if (this.userPrompt) {
            messages.push({ content: this.userPrompt, role: 'human', sources: [] });
        }
        messages.push(this.message);
        this.pdfService.exportConversationToPdf(messages, this.userPrompt || 'Response');
    }
}
