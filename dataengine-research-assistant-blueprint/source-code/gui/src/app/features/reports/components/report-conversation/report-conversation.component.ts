import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { ChatComponent } from '../chat/chat.component';
import { ReportPageStoreService } from '../../services/report-page-store.service';
import { MessageAiComponent } from '../../../conversation/components/message-ai/message-ai.component';
import { MessageHumanComponent } from '../../../shared/components/message-human/message-human.component';
import { ThinkItemComponent } from '../think-item/think-item.component';
import { ThinkBlockComponent } from '../think-block/think-block.component';
import { MatIcon } from '@angular/material/icon';
import { MatProgressSpinner } from '@angular/material/progress-spinner';
import { AnimationCrontrolService } from '../../../shared/services/animation-crontrol.service';
import { AsyncPipe } from '@angular/common';
import { AutoScrollDirective } from '../../../shared/directives/auto-scroll.component';
import { CollectionSelectorComponent } from "../../../conversation/components/collection-selector/collection-selector.component";

@Component({
  selector: 'app-report-conversation',
  standalone: true,
    imports: [
    ChatComponent,
    MessageAiComponent,
    MessageHumanComponent,
    ThinkItemComponent,
    ThinkBlockComponent,
    MatIcon,
    MatProgressSpinner,
    AsyncPipe,
    AutoScrollDirective,
    CollectionSelectorComponent
],
  templateUrl: './report-conversation.component.html',
  styleUrl: './report-conversation.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ReportConversationComponent {
    standalone = input<boolean>(false);

    store = inject(ReportPageStoreService);

    animFinishedService = inject(AnimationCrontrolService)

    aaa = false;

    animateScroll = computed(() => {
        if (!this.store.chatHistory()[this.store.chatHistory().length - 1].thinking) {
            return
        }
    })

    chatHistoryComputed = computed(() => {
        return this.store.chatHistory();
    })

    historicalMessages = computed(() => {
        const messages = this.chatHistoryComputed();
        return messages.slice(0, messages.length - this.lastMessages().length);
    });

    lastMessages = computed(() => {
        const messages = this.chatHistoryComputed();
        if (messages.length > 2) {
            const indexFromEnd = [...messages].reverse().findIndex((message: any) => message.role === 'human');
            const lastIndex = indexFromEnd === -1 ? -1 : messages.length - 1 - indexFromEnd;
            return lastIndex > -1 ? messages.slice(lastIndex) : [];
        } else {
            return messages;
        }
    });

    getPrecedingUserPrompt(aiIndex: number): string {
        const messages = this.chatHistoryComputed();
        for (let i = aiIndex - 1; i >= 0; i--) {
            if (messages[i].role === 'human') {
                const content = messages[i].content;
                return typeof content === 'string' ? content : '';
            }
        }
        return '';
    }
}
