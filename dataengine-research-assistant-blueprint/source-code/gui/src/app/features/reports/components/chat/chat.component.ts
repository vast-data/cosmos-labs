import { ChangeDetectionStrategy, Component, EventEmitter, inject, Input, OnInit, Output, signal } from '@angular/core';
import { MatIcon } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';
import { CollectionSelectorComponent } from "../../../conversation/components/collection-selector/collection-selector.component";
import { Collection } from '../../../shared/models/collections.model';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { SystemPromptService } from '../../../shared/services/system-prompt.service';

@Component({
    selector: 'app-chat',
    standalone: true,
    imports: [
    MatIcon,
    MatTooltipModule,
    FormsModule,
    CollectionSelectorComponent,
    MatFormFieldModule,
    MatInputModule,
],
    templateUrl: './chat.component.html',
    styleUrl: './chat.component.scss',
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class ChatComponent implements OnInit {
    promptService = inject(SystemPromptService);
    
    @Input() createNewMode = false;
    @Input() transparentMode = false;
    @Output() submitMessage = new EventEmitter<{ message: string, deepThinking: boolean, internetSearch: boolean, collection: Collection | null, systemPrompt: string | null }>();
    @Output() createNew = new EventEmitter<void>();

    focused = false;
    message = '';

    selectedCollection = signal<Collection | null>(null);
    isDeepThinkingEnabled = signal(false);
    isInternetSearchEnabled = signal(false);
    
    ngOnInit(): void {
        this.promptService.loadSystemPrompt();
    }

    toggleDeepResearch(): void {
        this.promptService.toggleDeepResearch();
    }

    toggleInternetSearch(): void {
        this.isInternetSearchEnabled.update(value => !value);
    }

    onSubmit() {
        if (this.message && this.selectedCollection()) {
            this.submitMessage.emit({
                message: this.message,
                deepThinking: this.isDeepThinkingEnabled(),
                internetSearch: this.isInternetSearchEnabled(),
                collection: this.selectedCollection(),
                systemPrompt: this.promptService.getEffectivePrompt()
            });
            this.message = '';
        }
    }

    onCreateNew() {
        this.createNew.emit();
    }

    onCollectionSelected(collection: Collection) {
        this.selectedCollection.set(collection);
    }
}
