import { ChangeDetectionStrategy, Component } from '@angular/core';
import { MatIcon } from '@angular/material/icon';

@Component({
    selector: 'app-markdown-clipboard',
    standalone: true,
    imports: [
        MatIcon
    ],
    templateUrl: './markdown-clipboard.component.html',
    styleUrl: './markdown-clipboard.component.scss',
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class MarkdownClipboardComponent {

}
