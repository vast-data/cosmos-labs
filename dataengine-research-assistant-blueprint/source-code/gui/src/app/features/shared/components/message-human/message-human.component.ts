import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { UserLogoComponent } from '../user-logo/user-logo.component';
import { ChatMessage, MessageContentBlock } from '../../../reports/services/session.mapper';

@Component({
  selector: 'app-message-human',
  standalone: true,
  imports: [
    UserLogoComponent
  ],
  templateUrl: './message-human.component.html',
  styleUrl: './message-human.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MessageHumanComponent {
  @Input() message: ChatMessage | null = null;

  get textContent(): string {
    if (!this.message) return '';
    
    if (typeof this.message.content === 'string') {
      return this.message.content;
    }
    
    // Extract text from content blocks
    return this.message.content
      .filter((block): block is MessageContentBlock & { type: 'text' } => block.type === 'text')
      .map(block => block.text)
      .join('');
  }
}
