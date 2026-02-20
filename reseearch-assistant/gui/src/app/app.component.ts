import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { IconsModule } from './features/shared/icons/icons.module';
import { MarkdownService } from 'ngx-markdown';
import { AiResponseStreamHttpService } from './features/reports/services/ai-response-stream.service';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [RouterOutlet, IconsModule],
    templateUrl: './app.component.html',
    styleUrl: './app.component.scss',
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class AppComponent implements OnInit {
    constructor(private markdownService: MarkdownService, private AiResponseStreamHttpService: AiResponseStreamHttpService) {
    }

    ngOnInit() {
        this.markdownService.renderer.code = (code, language) => {
            // language attr is hack to avoid name of lang in copied text
            const langLabel = language ? `<div class="code-language" language="${language}"></div>` : '';
            return `
    <div class="code-block">
      <pre>${langLabel}<code class="language-${language}">${code}</code></pre>
    </div>
  `;
        };
    }
}
