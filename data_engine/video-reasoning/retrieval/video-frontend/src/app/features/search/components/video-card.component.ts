import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { VideoSearchResult } from '../../../shared/models/video.model';

@Component({
  selector: 'app-video-card',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatChipsModule, MatButtonModule],
  template: `
    <mat-card class="video-card" (click)="onPlay()">
      <div class="card-header">
        <div class="similarity-score">
          <span class="score-label">Match</span>
          <span class="score-value">{{ (video.similarity_score * 100).toFixed(1) }}%</span>
        </div>
      </div>

      <mat-card-content>
        <h3 class="video-title">{{ video.filename }}</h3>
        
        <div class="reasoning-content">
          <mat-icon class="reasoning-icon">psychology</mat-icon>
          <p>{{ video.reasoning_content }}</p>
        </div>

        <div class="video-metadata">
          <span class="metadata-item">
            <mat-icon>movie</mat-icon>
            Segment {{ video.segment_number }}/{{ video.total_segments }}
          </span>
          <span class="metadata-item">
            <mat-icon>schedule</mat-icon>
            {{ video.duration }}s
          </span>
          @if (video.is_public) {
            <span class="metadata-item public">
              <mat-icon>public</mat-icon>
              Public
            </span>
          } @else {
            <span class="metadata-item private">
              <mat-icon>lock</mat-icon>
              Private
            </span>
          }
        </div>

        @if (video.tags && video.tags.length > 0) {
          <div class="tags-container">
            <mat-chip-set class="tags">
              @for (tag of video.tags; track tag) {
                <mat-chip>{{ tag }}</mat-chip>
              }
            </mat-chip-set>
          </div>
        }
      </mat-card-content>

      <mat-card-actions>
        <button mat-raised-button color="primary" (click)="onPlay(); $event.stopPropagation()">
          <mat-icon>play_arrow</mat-icon>
          Play Video
        </button>
      </mat-card-actions>
    </mat-card>
  `,
  styles: [`
    .video-card {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      cursor: pointer;
      transition: all 0.3s ease;
      overflow: hidden;
      
      &:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
        border-color: rgba(102, 126, 234, 0.5);
      }
    }

    .card-header {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      padding: 1rem 1rem 0;
    }

    .similarity-score {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      background: rgba(102, 126, 234, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 12px;
      border: 1px solid rgba(102, 126, 234, 0.3);
      
      .score-label {
        font-size: 0.7rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
      }
      
      .score-value {
        font-size: 1.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #06ffa5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }
    }

    ::ng-deep .mat-mdc-card-content {
      padding: 1rem;
    }

    .video-title {
      color: #fff;
      font-size: 1rem;
      font-weight: 600;
      margin: 0 0 1rem 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .reasoning-content {
      display: flex;
      gap: 0.75rem;
      align-items: flex-start;
      background: rgba(6, 255, 165, 0.05);
      border: 1px solid rgba(6, 255, 165, 0.2);
      border-radius: 12px;
      padding: 0.75rem;
      margin-bottom: 1rem;
      
      .reasoning-icon {
        color: rgba(6, 255, 165, 0.8);
        font-size: 1.25rem;
      }
      
      p {
        margin: 0;
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.9rem;
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
    }

    .video-metadata {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-bottom: 1rem;
      
      .metadata-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.7);
        background: rgba(255, 255, 255, 0.03);
        padding: 0.25rem 0.75rem;
        border-radius: 8px;
        
        mat-icon {
          font-size: 1rem;
          width: 1rem;
          height: 1rem;
        }
        
        &.public {
          background: rgba(6, 255, 165, 0.1);
          color: rgba(6, 255, 165, 0.9);
          border: 1px solid rgba(6, 255, 165, 0.3);
        }
        
        &.private {
          background: rgba(255, 193, 7, 0.1);
          color: rgba(255, 193, 7, 0.9);
          border: 1px solid rgba(255, 193, 7, 0.3);
        }
      }
    }

    .tags-container {
      margin-bottom: 0.5rem;
    }

    .tags {
      ::ng-deep mat-chip {
        background: rgba(102, 126, 234, 0.1);
        color: rgba(102, 126, 234, 0.9);
        border: 1px solid rgba(102, 126, 234, 0.2);
        font-size: 0.75rem;
      }
    }

    ::ng-deep mat-card-actions {
      padding: 0 1rem 1rem;
      
      button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        
        &:hover {
          box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
      }
    }
  `]
})
export class VideoCardComponent {
  @Input({ required: true }) video!: VideoSearchResult;
  @Output() play = new EventEmitter<VideoSearchResult>();

  onPlay() {
    this.play.emit(this.video);
  }
}

