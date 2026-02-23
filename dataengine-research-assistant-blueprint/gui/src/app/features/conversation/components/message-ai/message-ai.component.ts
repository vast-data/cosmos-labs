import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    Output,
    AfterViewInit
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { StringToFlowPipe } from '../../../shared/pipes/string-to-flow.pipe';
import { MarkdownViewerComponent } from '../../../shared/components/markdown-viewer/markdown-viewer.component';
import { ToolBlockComponent } from '../tool-block/tool-block.component';
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
        ToolBlockComponent
    ],
    templateUrl: './message-ai.component.html',
    styleUrl: './message-ai.component.scss',
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class MessageAiComponent implements AfterViewInit {
    private _animate = false;

    @Input() set animate(val: boolean) {
        if (!this._animate) this._animate = val;
    }
    get animate() { return this._animate; }

    @Input() message: ChatMessage | null = null;
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
}
