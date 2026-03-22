import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { LLMSynthesis } from '../../../shared/models/video.model';

@Component({
  selector: 'app-llm-synthesis',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatTooltipModule],
  template: `
    <div class="synthesis-container" *ngIf="synthesis">
      <div class="synthesis-header">
        <div class="header-content">
          <mat-icon class="ai-icon">auto_awesome</mat-icon>
          <h3>Top {{synthesis.segments_used}} Segments LLM-Summary</h3>
          <span class="badge">Powered by {{synthesis.model}}</span>
        </div>
        <div class="header-meta">
          <span class="meta-item" [matTooltip]="'Analyzed ' + synthesis.segments_used + ' video segments'">
            <mat-icon>videocam</mat-icon>
            {{synthesis.segments_used}} segments
          </span>
          <span class="meta-item" [matTooltip]="'Processing time'">
            <mat-icon>schedule</mat-icon>
            {{synthesis.processing_time}}s
          </span>
          <span class="meta-item" [matTooltip]="'Tokens used'">
            <mat-icon>data_usage</mat-icon>
            {{synthesis.tokens_used}} tokens
          </span>
        </div>
      </div>
      
      <div class="synthesis-content" [class.error]="synthesis.error">
        <div *ngIf="!synthesis.error">
          <div class="response-text" [innerHTML]="formatResponse(synthesis.response)"></div>
          <div class="segments-list" *ngIf="synthesis.segments_analyzed && synthesis.segments_analyzed.length > 0">
            <button class="segments-toggle" (click)="showSegments = !showSegments">
              <mat-icon>movie_filter</mat-icon>
              <span>Segments Analyzed ({{synthesis.segments_analyzed.length}})</span>
              <mat-icon class="toggle-icon" [class.expanded]="showSegments">expand_more</mat-icon>
            </button>
            <div class="segment-chips" *ngIf="showSegments">
              <span class="segment-chip" *ngFor="let segment of synthesis.segments_analyzed">
                {{segment}}
              </span>
            </div>
          </div>
        </div>
        <div *ngIf="synthesis.error" class="error-message">
          <mat-icon>error_outline</mat-icon>
          <span>{{synthesis.error}}</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .synthesis-container {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      backdrop-filter: blur(10px);
      box-shadow: var(--shadow);
      animation: slideIn 0.3s ease-out;
      transition: background 0.3s ease, border-color 0.3s ease;
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(-10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .synthesis-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      flex-wrap: wrap;
      gap: 1rem;

      .header-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;

        .ai-icon {
          color: #00d9ff;
          font-size: 28px;
          width: 28px;
          height: 28px;
          filter: drop-shadow(0 0 8px rgba(0, 217, 255, 0.6));
        }

        h3 {
          margin: 0;
          color: var(--text-primary);
          font-size: 1.25rem;
          font-weight: 600;
        }

        .badge {
          background: var(--bg-secondary);
          color: var(--text-primary);
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 500;
          border: 1px solid var(--border-color);
          transition: background 0.3s ease, color 0.3s ease, border-color 0.3s ease;
        }
      }

      .header-meta {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          color: var(--text-secondary);
          font-size: 0.875rem;
          cursor: help;

          mat-icon {
            font-size: 16px;
            width: 16px;
            height: 16px;
            color: var(--accent-primary);
          }

          &:hover {
            color: var(--text-primary);
          }
        }
      }
    }

    .synthesis-content {
      background: var(--bg-secondary);
      border-radius: 12px;
      padding: 1.25rem;
      border: 1px solid var(--border-color);
      transition: background 0.3s ease, border-color 0.3s ease;

      &.error {
        border-color: var(--accent-danger);
        background: rgba(255, 82, 82, 0.1);
      }

      .response-text {
        color: var(--text-primary);
        font-size: 1rem;
        line-height: 1.7;
        word-wrap: break-word;
        margin-bottom: 1rem;

        h4 {
          color: var(--accent-primary);
          font-size: 1.1rem;
          font-weight: 600;
          margin: 1rem 0 0.5rem 0;
          padding-bottom: 0.25rem;
          border-bottom: 1px solid var(--border-color);
        }

        h4:first-child {
          margin-top: 0;
        }

        h5 {
          color: var(--text-primary);
          font-size: 1rem;
          font-weight: 600;
          margin: 0.75rem 0 0.4rem 0;
        }

        p {
          margin: 0.5rem 0;
        }

        ul {
          margin: 0.5rem 0;
          padding-left: 1.5rem;
          list-style: none;
        }

        li {
          position: relative;
          margin: 0.4rem 0;
          padding-left: 0.5rem;
        }

        li::before {
          content: '•';
          position: absolute;
          left: -1rem;
          color: var(--accent-primary);
          font-weight: bold;
        }

        strong {
          color: var(--text-primary);
          font-weight: 600;
        }

        em {
          font-style: italic;
          color: var(--text-secondary);
        }
      }

      .segments-list {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
        transition: border-color 0.3s ease;

        .segments-toggle {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: var(--accent-primary);
          font-size: 0.875rem;
          font-weight: 500;
          background: transparent;
          border: none;
          cursor: pointer;
          padding: 0.5rem 0.75rem;
          border-radius: 8px;
          transition: background 0.2s ease;
          width: 100%;
          text-align: left;

          &:hover {
            background: var(--bg-card);
          }

          mat-icon {
            font-size: 18px;
            width: 18px;
            height: 18px;
          }

          .toggle-icon {
            margin-left: auto;
            transition: transform 0.2s ease;

            &.expanded {
              transform: rotate(180deg);
            }
          }
        }

        .segment-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-top: 0.75rem;
          padding-left: 0.75rem;
          animation: fadeIn 0.2s ease;

          .segment-chip {
            background: var(--bg-secondary);
            color: var(--text-primary);
            padding: 0.4rem 0.75rem;
            border-radius: 8px;
            font-size: 0.8rem;
            border: 1px solid var(--border-color);
            font-family: 'Roboto Mono', monospace;
            transition: background 0.3s ease, color 0.3s ease, border-color 0.3s ease;
          }
        }
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(-5px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .error-message {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: #ff5252;

        mat-icon {
          font-size: 24px;
          width: 24px;
          height: 24px;
        }

        span {
          font-size: 0.95rem;
        }
      }
    }

    @media (max-width: 768px) {
      .synthesis-header {
        flex-direction: column;
        align-items: flex-start;

        .header-meta {
          width: 100%;
        }
      }
    }
  `]
})
export class LLMSynthesisComponent {
  @Input() synthesis: LLMSynthesis | null = null;
  showSegments = false;

  formatResponse(text: string): string {
    if (!text) return '';
    
    let formatted = text
      // Escape HTML to prevent XSS
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      // Headers: **Title** or ## Title at start of line
      .replace(/^\*\*(.+?)\*\*$/gm, '<h4>$1</h4>')
      .replace(/^##\s+(.+)$/gm, '<h4>$1</h4>')
      .replace(/^###\s+(.+)$/gm, '<h5>$1</h5>')
      // Bold: **text** or __text__
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/__(.+?)__/g, '<strong>$1</strong>')
      // Italic: *text* or _text_
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/_([^_]+)_/g, '<em>$1</em>')
      // Bullet points: - item or * item at start of line
      .replace(/^[\-\*]\s+(.+)$/gm, '<li>$1</li>')
      // Numbered lists: 1. item, 2. item, etc.
      .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
      // Wrap consecutive <li> elements in <ul>
      .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
      // Line breaks
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');
    
    // Wrap in paragraph if not starting with a block element
    if (!formatted.startsWith('<h') && !formatted.startsWith('<ul')) {
      formatted = '<p>' + formatted + '</p>';
    }
    
    return formatted;
  }
}

