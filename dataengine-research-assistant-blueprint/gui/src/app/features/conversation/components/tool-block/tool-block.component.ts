import {
  ChangeDetectionStrategy,
  Component,
  Input,
  signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIcon } from '@angular/material/icon';
import { ToolContentBlock } from '../../../reports/services/session.mapper';
import { formatDuration } from '../../../reports/utils/stream-event.utils';

@Component({
  selector: 'app-tool-block',
  standalone: true,
  imports: [CommonModule, MatIcon],
  templateUrl: './tool-block.component.html',
  styleUrl: './tool-block.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ToolBlockComponent {
  @Input({ required: true }) tool!: ToolContentBlock;

  expanded = signal(false);

  toggle(): void {
    this.expanded.update(v => !v);
  }

  get displayName(): string {
    return this.formatToolName(this.tool.toolName);
  }

  get durationText(): string {
    if (this.tool.status === 'loading') {
      return 'Running...';
    }
    return this.tool.duration ? formatDuration(this.tool.duration) : '';
  }

  get citationsCount(): number {
    return this.tool.citations?.length ?? 0;
  }

  get chunksCount(): number {
    return this.tool.chunks?.length ?? 0;
  }

  get hasExpandableContent(): boolean {
    return !!this.tool.prompt || !!this.queryText || !!this.metadataQueryText || this.citationsCount > 0 || this.chunksCount > 0;
  }

  get queryText(): string | null {
    // Get prompt or query from arguments
    const args = this.tool.arguments;
    if (!args) return null;
    return (args['prompt'] as string) || (args['query'] as string) || (args['similarity_query'] as string) || null;
  }

  get metadataQueryText(): string | null {
    // Get metadata_query_used from tool result or from arguments
    if (this.tool.metadataQueryUsed) return this.tool.metadataQueryUsed;
    const args = this.tool.arguments;
    if (!args) return null;
    const mq = args['metadata_query'] as string;
    return mq && mq.trim() ? mq : null;
  }

  get isWarning(): boolean {
    return this.tool.status === 'warning';
  }

  get errorMessage(): string | null {
    return this.tool.error ?? null;
  }

  private formatToolName(name: string): string {
    // Display "RAG Results" instead of "Retrieve Chunks" for the retrieve_chunks tool
    if (name === 'retrieve_chunks') {
      return 'RAG Results';
    }
    if (name === 'hybrid_query') {
      return 'Hybrid Metadata Analysis';
    }
    return name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, char => char.toUpperCase());
  }

  /** Build a map from source-title → source-url using chunks data */
  get citationUrlMap(): Record<string, string> {
    const map: Record<string, string> = {};
    if (this.tool.chunks) {
      for (const chunk of this.tool.chunks) {
        if (chunk.sourceTitle && chunk.sourceUrl && !map[chunk.sourceTitle]) {
          map[chunk.sourceTitle] = chunk.sourceUrl;
        }
      }
    }
    return map;
  }

  getCitationUrl(citation: string): string | null {
    return this.citationUrlMap[citation] ?? null;
  }

  truncateText(text: string, maxLength = 200): string {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  }
}

