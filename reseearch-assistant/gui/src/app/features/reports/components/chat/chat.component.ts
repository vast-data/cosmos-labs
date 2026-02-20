import { ChangeDetectionStrategy, Component, EventEmitter, inject, Input, OnInit, Output, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MatIcon } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';
import { CollectionSelectorComponent } from "../../../conversation/components/collection-selector/collection-selector.component";
import { Collection } from '../../../shared/models/collections.model';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { SETTINGS } from '../../../shared/settings';

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
    private http = inject(HttpClient);
    
    @Input() createNewMode = false;
    @Input() transparentMode = false;
    @Output() submitMessage = new EventEmitter<{ message: string, deepThinking: boolean, internetSearch: boolean, collection: Collection | null, systemPrompt: string | null }>();
    @Output() createNew = new EventEmitter<void>();

    focused = false;
    message = '';

    selectedCollection = signal<Collection | null>(null);
    isDeepThinkingEnabled = signal(false);
    isInternetSearchEnabled = signal(false);
    isSystemPromptExpanded = signal(false);
    defaultSystemPrompt = signal('');
    customSystemPrompt = signal('');
    
    ngOnInit(): void {
        // Load default system prompt from backend
        this.http.get<{ system_prompt: string }>(`${SETTINGS.BASE_API_URL}/system-prompt`).subscribe({
            next: (response) => {
                this.defaultSystemPrompt.set(response.system_prompt);
                this.customSystemPrompt.set(response.system_prompt);
            },
            error: (err) => console.error('Failed to load system prompt:', err)
        });
    }
    
    toggleSystemPrompt(): void {
        this.isSystemPromptExpanded.update(value => !value);
    }
    
    resetSystemPrompt(): void {
        this.customSystemPrompt.set(this.defaultSystemPrompt());
    }
    
    hasCustomSystemPrompt(): boolean {
        return this.customSystemPrompt() !== this.defaultSystemPrompt();
    }

    toggleDeepThinking(): void {
        this.isDeepThinkingEnabled.update(value => !value);
    }

    toggleInternetSearch(): void {
        this.isInternetSearchEnabled.update(value => !value);
    }

    onSubmit() {
        if (this.message) {
            // Only send custom system prompt if it differs from default
            const systemPrompt = this.hasCustomSystemPrompt() ? this.customSystemPrompt() : null;
            
            this.submitMessage.emit({
                message: this.message,
                deepThinking: this.isDeepThinkingEnabled(),
                internetSearch: this.isInternetSearchEnabled(),
                collection: this.selectedCollection(),
                systemPrompt: systemPrompt
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
