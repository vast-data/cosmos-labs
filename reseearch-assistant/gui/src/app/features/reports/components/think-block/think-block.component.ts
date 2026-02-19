import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatExpansionModule } from '@angular/material/expansion';
import { MarkdownViewerComponent } from '../../../shared/components/markdown-viewer/markdown-viewer.component';

interface PanelItem {
    title: string;
    description: string;
    time: string;
    content: string;
    status: 'success' | 'pending' | 'error';
}
@Component({
    selector: 'app-think-block',
    standalone: true,
    imports: [MatExpansionModule, MatIconModule, CommonModule, MarkdownViewerComponent],
    templateUrl: './think-block.component.html',
    styleUrl: './think-block.component.scss',
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class ThinkBlockComponent {
    @Input() items: PanelItem[] = [];

    opened = true
}
