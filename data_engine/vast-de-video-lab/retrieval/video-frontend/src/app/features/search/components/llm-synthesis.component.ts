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
          <div class="response-text">
            {{synthesis.response}}
          </div>
          <div class="segments-list" *ngIf="synthesis.segments_analyzed && synthesis.segments_analyzed.length > 0">
            <div class="segments-header">
              <mat-icon>movie_filter</mat-icon>
              <span>Segments Analyzed:</span>
            </div>
            <div class="segment-chips">
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
      background: linear-gradient(135deg, rgba(0, 71, 171, 0.15) 0%, rgba(0, 51, 128, 0.15) 100%);
      border: 1px solid rgba(0, 217, 255, 0.3);
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      backdrop-filter: blur(10px);
      box-shadow: 
        0 8px 32px rgba(0, 71, 171, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
      animation: slideIn 0.3s ease-out;
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
          color: #ffffff;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .badge {
          background: rgba(0, 71, 171, 0.3);
          color: rgba(255, 255, 255, 0.9);
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 500;
          border: 1px solid rgba(0, 71, 171, 0.5);
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
          color: rgba(255, 255, 255, 0.7);
          font-size: 0.875rem;
          cursor: help;

          mat-icon {
            font-size: 16px;
            width: 16px;
            height: 16px;
            color: #00d9ff;
          }

          &:hover {
            color: rgba(255, 255, 255, 0.9);
          }
        }
      }
    }

    .synthesis-content {
      background: rgba(10, 10, 30, 0.5);
      border-radius: 12px;
      padding: 1.25rem;
      border: 1px solid rgba(0, 217, 255, 0.15);

      &.error {
        border-color: rgba(255, 82, 82, 0.5);
        background: rgba(255, 82, 82, 0.1);
      }

      .response-text {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1rem;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
        margin-bottom: 1rem;
      }

      .segments-list {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(0, 217, 255, 0.2);

        .segments-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: rgba(0, 217, 255, 0.9);
          font-size: 0.875rem;
          font-weight: 500;
          margin-bottom: 0.75rem;

          mat-icon {
            font-size: 18px;
            width: 18px;
            height: 18px;
          }
        }

        .segment-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;

          .segment-chip {
            background: rgba(0, 71, 171, 0.3);
            color: rgba(255, 255, 255, 0.9);
            padding: 0.4rem 0.75rem;
            border-radius: 8px;
            font-size: 0.8rem;
            border: 1px solid rgba(0, 217, 255, 0.3);
            font-family: 'Roboto Mono', monospace;
          }
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
}

