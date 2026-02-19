import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { MarkdownViewerComponent } from '../../../shared/components/markdown-viewer/markdown-viewer.component';

@Component({
  selector: 'app-report-view',
  standalone: true,
    imports: [
        MarkdownViewerComponent
    ],
  templateUrl: './report-view.component.html',
  styleUrl: './report-view.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ReportViewComponent {
    content = input('');
    responding = input(false);

}
