import { Component, Inject, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { VideoSearchResult } from '../../shared/models/video.model';
import { VideoService } from '../../shared/services/video.service';

@Component({
  selector: 'app-video-player',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTooltipModule
  ],
  template: `
    <div class="video-player-container">
      <div class="player-header">
        <h2>{{ data.video.filename }}</h2>
        <button mat-icon-button (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="player-content">
        <div class="video-wrapper">
          @if (loading()) {
            <div class="loading-overlay">
              <mat-spinner></mat-spinner>
              <p>Loading video...</p>
            </div>
          }
          
          @if (streamUrl() && !error()) {
            <video 
              #videoPlayer
              [src]="streamUrl()"
              controls
              autoplay
              (loadeddata)="onVideoLoaded()"
              (error)="onVideoError($event)"
              class="video-player">
              Your browser does not support the video tag.
            </video>
          }

          @if (error()) {
            <div class="error-state">
              <mat-icon>error_outline</mat-icon>
              <p>{{ error() }}</p>
              <button mat-raised-button color="primary" (click)="loadVideo()">
                <mat-icon>refresh</mat-icon>
                Retry
              </button>
            </div>
          }
        </div>

        <div class="video-info">
          <div class="segment-nav">
            <h3>Segment Navigation</h3>
            <div class="segment-controls">
              <button 
                mat-icon-button 
                (click)="previousSegment()"
                [disabled]="isFirstSegment()"
                matTooltip="Previous segment">
                <mat-icon>skip_previous</mat-icon>
              </button>
              <span class="segment-indicator">
                Segment {{ data.video.segment_number }} of {{ data.video.total_segments }}
              </span>
              <button 
                mat-icon-button 
                (click)="nextSegment()"
                [disabled]="isLastSegment()"
                matTooltip="Next segment">
                <mat-icon>skip_next</mat-icon>
              </button>
            </div>
          </div>

          <div class="reasoning-panel">
            <h3>
              <mat-icon>psychology</mat-icon>
              AI Reasoning
            </h3>
            <p class="reasoning-text">{{ data.video.reasoning_content }}</p>
            
            <div class="metadata-grid">
              <div class="metadata-item">
                <span class="label">Model:</span>
                <span class="value">{{ data.video.cosmos_model }}</span>
              </div>
              <div class="metadata-item">
                <span class="label">Tokens:</span>
                <span class="value">{{ data.video.tokens_used }}</span>
              </div>
              <div class="metadata-item">
                <span class="label">Duration:</span>
                <span class="value">{{ data.video.duration }}s</span>
              </div>
              <div class="metadata-item">
                <span class="label">Timestamp:</span>
                <span class="value">{{ formatTimestamp(data.video.upload_timestamp) }}</span>
              </div>
              <div class="metadata-item">
                <span class="label">Visibility:</span>
                <span class="value">{{ data.video.is_public ? 'Public' : 'Private' }}</span>
              </div>
              @if (data.video.tags && data.video.tags.length > 0) {
                <div class="metadata-item full-width">
                  <span class="label">Tags:</span>
                  <span class="value tags">
                    @for (tag of data.video.tags; track tag) {
                      <span class="tag">{{ tag }}</span>
                    }
                  </span>
                </div>
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .video-player-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: #0f0f1e;
      color: #fff;
    }

    .player-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.5rem;
      background: rgba(255, 255, 255, 0.03);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      
      h2 {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
      }
      
      button {
        color: #fff;
      }
    }

    .player-content {
      flex: 1;
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.5rem;
      padding: 1.5rem;
      overflow: auto;
    }

    .video-wrapper {
      position: relative;
      background: #000;
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .video-player {
      width: 100%;
      height: auto;
      max-height: 70vh;
    }

    .loading-overlay {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.8);
      gap: 1rem;
      
      p {
        color: rgba(255, 255, 255, 0.8);
      }
    }

    .error-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 1rem;
      padding: 3rem;
      
      mat-icon {
        font-size: 4rem;
        width: 4rem;
        height: 4rem;
        color: #ef4444;
      }
      
      p {
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
      }
    }

    .video-info {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .segment-nav {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 1.5rem;
      
      h3 {
        margin: 0 0 1rem 0;
        font-size: 1rem;
        color: rgba(102, 126, 234, 0.9);
      }
      
      .segment-controls {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        
        button {
          color: #fff;
          
          &:disabled {
            opacity: 0.3;
          }
        }
        
        .segment-indicator {
          font-weight: 600;
          padding: 0.5rem 1rem;
          background: rgba(102, 126, 234, 0.1);
          border-radius: 8px;
        }
      }
    }

    .reasoning-panel {
      background: rgba(6, 255, 165, 0.05);
      border: 1px solid rgba(6, 255, 165, 0.2);
      border-radius: 12px;
      padding: 1.5rem;
      flex: 1;
      
      h3 {
        margin: 0 0 1rem 0;
        font-size: 1rem;
        color: rgba(6, 255, 165, 0.9);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        
        mat-icon {
          font-size: 1.25rem;
          width: 1.25rem;
          height: 1.25rem;
        }
      }
      
      .reasoning-text {
        color: rgba(255, 255, 255, 0.9);
        line-height: 1.6;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
      }
    }

    .metadata-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
      
      .metadata-item {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        padding: 0.75rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        
        &.full-width {
          grid-column: 1 / -1;
        }
        
        .label {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.5);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        
        .value {
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.9);
          font-family: 'Courier New', monospace;
          
          &.tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            
            .tag {
              background: rgba(102, 126, 234, 0.1);
              color: rgba(102, 126, 234, 0.9);
              padding: 0.25rem 0.75rem;
              border-radius: 6px;
              font-size: 0.8rem;
            }
          }
        }
      }
    }

    @media (max-width: 900px) {
      .player-content {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class VideoPlayerComponent implements OnInit {
  private videoService = inject(VideoService);
  private sanitizer = inject(DomSanitizer);
  private dialogRef = inject(MatDialogRef<VideoPlayerComponent>);

  loading = signal(true);
  error = signal<string | null>(null);
  streamUrl = signal<SafeResourceUrl | null>(null);

  constructor(@Inject(MAT_DIALOG_DATA) public data: { video: VideoSearchResult }) {}

  ngOnInit() {
    this.loadVideo();
  }

  loadVideo() {
    this.loading.set(true);
    this.error.set(null);

    try {
      console.log('[VIDEO PLAYER] Requesting stream URL for:', this.data.video.source);
      
      // Get token from localStorage (using correct key: 'video_lab_token')
      const token = localStorage.getItem('video_lab_token');
      if (!token) {
        const errorMsg = 'No authentication token found in localStorage (key: video_lab_token)';
        console.error('[VIDEO PLAYER]', errorMsg);
        console.error('[VIDEO PLAYER] Available localStorage keys:', Object.keys(localStorage));
        throw new Error(errorMsg);
      }
      
      console.log('[VIDEO PLAYER] Token found, length:', token.length);
      
      // Get backend stream URL with token (required for HTML5 video element)
      const streamUrl = this.videoService.getStreamUrl(this.data.video.source, token);
      console.log('[VIDEO PLAYER] Generated stream URL:', streamUrl);
      
      const sanitized = this.sanitizer.bypassSecurityTrustResourceUrl(streamUrl);
      this.streamUrl.set(sanitized);
      console.log('[VIDEO PLAYER] Stream URL set, waiting for video to load...');
    } catch (err: any) {
      console.error('[VIDEO PLAYER] Exception in loadVideo():', err);
      console.error('[VIDEO PLAYER] Error message:', err.message);
      console.error('[VIDEO PLAYER] Error stack:', err.stack);
      this.error.set(`Failed to load video stream: ${err.message}`);
      this.loading.set(false);
    }
  }

  onVideoLoaded() {
    console.log('[VIDEO PLAYER] Video loaded successfully');
    this.loading.set(false);
  }

  onVideoError(event?: any) {
    console.error('[VIDEO PLAYER] Video element error:', event);
    console.error('[VIDEO PLAYER] Video element error code:', (event?.target as HTMLVideoElement)?.error?.code);
    console.error('[VIDEO PLAYER] Video element error message:', (event?.target as HTMLVideoElement)?.error?.message);
    this.error.set('Failed to load video. Please try again.');
    this.loading.set(false);
  }

  isFirstSegment(): boolean {
    return this.data.video.segment_number === 1;
  }

  isLastSegment(): boolean {
    return this.data.video.segment_number === this.data.video.total_segments;
  }

  async previousSegment() {
    if (this.isFirstSegment()) return;
    
    // Calculate the previous segment filename
    const currentSegment = this.data.video.segment_number;
    const previousSegmentNumber = currentSegment - 1;
    
    // Replace segment number in the source and filename
    const newSource = this.data.video.source.replace(
      `_segment_${String(currentSegment).padStart(3, '0')}_of_`,
      `_segment_${String(previousSegmentNumber).padStart(3, '0')}_of_`
    );
    
    console.log('[VIDEO PLAYER] Loading previous segment:', previousSegmentNumber);
    console.log('[VIDEO PLAYER] Fetching metadata for:', newSource);
    
    // Fetch metadata for the new segment from backend
    try {
      const metadata = await this.videoService.getVideoMetadata(newSource).toPromise();
      
      // Update all video data with new segment metadata
      this.data.video = {
        ...this.data.video,
        ...metadata,
        source: newSource,
        segment_number: previousSegmentNumber
      };
      
      console.log('[VIDEO PLAYER] Metadata updated for segment', previousSegmentNumber);
      this.loadVideo();
    } catch (err) {
      console.error('[VIDEO PLAYER] Failed to fetch segment metadata:', err);
      // Fallback: just change video without updating metadata
      this.data.video.source = newSource;
      this.data.video.segment_number = previousSegmentNumber;
      this.loadVideo();
    }
  }

  async nextSegment() {
    if (this.isLastSegment()) return;
    
    // Calculate the next segment filename
    const currentSegment = this.data.video.segment_number;
    const nextSegmentNumber = currentSegment + 1;
    
    // Replace segment number in the source and filename
    const newSource = this.data.video.source.replace(
      `_segment_${String(currentSegment).padStart(3, '0')}_of_`,
      `_segment_${String(nextSegmentNumber).padStart(3, '0')}_of_`
    );
    
    console.log('[VIDEO PLAYER] Loading next segment:', nextSegmentNumber);
    console.log('[VIDEO PLAYER] Fetching metadata for:', newSource);
    
    // Fetch metadata for the new segment from backend
    try {
      const metadata = await this.videoService.getVideoMetadata(newSource).toPromise();
      
      // Update all video data with new segment metadata
      this.data.video = {
        ...this.data.video,
        ...metadata,
        source: newSource,
        segment_number: nextSegmentNumber
      };
      
      console.log('[VIDEO PLAYER] Metadata updated for segment', nextSegmentNumber);
      this.loadVideo();
    } catch (err) {
      console.error('[VIDEO PLAYER] Failed to fetch segment metadata:', err);
      // Fallback: just change video without updating metadata
      this.data.video.source = newSource;
      this.data.video.segment_number = nextSegmentNumber;
      this.loadVideo();
    }
  }

  formatTimestamp(timestamp: string): string {
    if (!timestamp) return 'N/A';
    
    try {
      const date = new Date(timestamp);
      
      // Format: "Nov 5, 2025 at 2:30 PM"
      const dateStr = date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
      
      const timeStr = date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
      
      return `${dateStr} at ${timeStr}`;
    } catch (error) {
      console.error('[VIDEO PLAYER] Error formatting timestamp:', error);
      return timestamp;
    }
  }

  close() {
    this.dialogRef.close();
  }
}

