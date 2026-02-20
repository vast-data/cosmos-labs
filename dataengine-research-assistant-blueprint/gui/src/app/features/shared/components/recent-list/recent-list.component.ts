import { ChangeDetectionStrategy, Component, computed, EventEmitter, input, Output } from '@angular/core';
import { MatIcon } from '@angular/material/icon';

@Component({
    selector: 'app-recent-list',
    standalone: true,
    imports: [
        MatIcon
    ],
    templateUrl: './recent-list.component.html',
    styleUrl: './recent-list.component.scss',
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class RecentListComponent {
    conversations = input<any[]>();
    selectedConversation = input<number | null>();

    @Output() selectConversation = new EventEmitter<number>();

    orderedConversations = computed(() => {
        return this.conversations()?.sort((a, b) => b.id - a.id);
    });
}
