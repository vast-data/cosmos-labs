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
      <!-- Header with filename and close -->
      <div class="player-header">
        <div class="header-info">
          <mat-icon class="video-icon">play_circle</mat-icon>
          <h2>{{ data.video.filename }}</h2>
        </div>
        <button mat-icon-button class="close-btn" (click)="close()" matTooltip="Close">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <!-- Segment Navigation - ABOVE video -->
      <div class="segment-nav-bar">
        <button 
          mat-icon-button 
          class="nav-btn"
          (click)="previousSegment()"
          [disabled]="isFirstSegment()"
          matTooltip="Previous segment">
          <mat-icon>skip_previous</mat-icon>
        </button>
        <div class="segment-info">
          <span class="segment-label">Segment</span>
          <span class="segment-number">{{ data.video.segment_number }}</span>
          <span class="segment-separator">of</span>
          <span class="segment-total">{{ data.video.total_segments }}</span>
        </div>
        <button 
          mat-icon-button 
          class="nav-btn"
          (click)="nextSegment()"
          [disabled]="isLastSegment()"
          matTooltip="Next segment">
          <mat-icon>skip_next</mat-icon>
        </button>
      </div>

      <!-- Video Player - CENTER -->
      <div class="video-section">
        @if (loading()) {
          <div class="loading-overlay">
            <mat-spinner diameter="48"></mat-spinner>
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

      <!-- Info Section - BELOW video -->
      <div class="info-section">
        <!-- AI Reasoning -->
        <div class="reasoning-card">
          <div class="card-header">
            <mat-icon>psychology</mat-icon>
            <h3>AI Scene Analysis</h3>
          </div>
          <p class="reasoning-text">{{ data.video.reasoning_content }}</p>
        </div>

        <!-- Metadata Grid -->
        <div class="metadata-section">
          <div class="metadata-row">
            <div class="meta-chip">
              <mat-icon>schedule</mat-icon>
              <span>{{ formatTimestamp(data.video.upload_timestamp) }}</span>
            </div>
            <div class="meta-chip">
              <mat-icon>timer</mat-icon>
              <span>{{ data.video.duration }}s duration</span>
            </div>
            <div class="meta-chip">
              <mat-icon>memory</mat-icon>
              <span>{{ data.video.cosmos_model }}</span>
            </div>
            <div class="meta-chip">
              <mat-icon>token</mat-icon>
              <span>{{ data.video.tokens_used }} tokens</span>
            </div>
            <div class="meta-chip" [class.public]="data.video.is_public" [class.private]="!data.video.is_public">
              <mat-icon>{{ data.video.is_public ? 'public' : 'lock' }}</mat-icon>
              <span>{{ data.video.is_public ? 'Public' : 'Private' }}</span>
            </div>
            @if (data.video.camera_id && data.video.camera_id.trim()) {
              <div class="meta-chip">
                <mat-icon>videocam</mat-icon>
                <span>{{ data.video.camera_id }}</span>
              </div>
            }
            @if (data.video.capture_type && data.video.capture_type.trim()) {
              <div class="meta-chip">
                <mat-icon>category</mat-icon>
                <span>{{ data.video.capture_type }}</span>
              </div>
            }
            @if (data.video.neighborhood && data.video.neighborhood.trim()) {
              <div class="meta-chip">
                <mat-icon>location_on</mat-icon>
                <span>{{ data.video.neighborhood }}</span>
              </div>
            }
          </div>
          
          @if (data.video.tags && data.video.tags.length > 0) {
            <div class="tags-row">
              <mat-icon class="tags-icon">label</mat-icon>
              @for (tag of data.video.tags; track tag) {
                <span class="tag-chip">{{ tag }}</span>
              }
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .video-player-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      max-height: 90vh;
      background: var(--bg-primary);
      color: var(--text-primary);
      overflow: hidden;
      transition: background 0.3s ease, color 0.3s ease;
    }

    /* Header */
    .player-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.75rem 1.25rem;
      background: var(--bg-card);
      border-bottom: 1px solid var(--border-color);
      flex-shrink: 0;
      transition: background 0.3s ease, border-color 0.3s ease;
      
      .header-info {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        
        .video-icon {
          color: var(--accent-primary);
          font-size: 1.5rem;
        }
        
        h2 {
          margin: 0;
          font-size: 1rem;
          font-weight: 500;
          color: var(--text-primary);
          max-width: 500px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }
      
      .close-btn {
        color: var(--text-secondary);
        transition: all 0.2s;
        
        &:hover {
          color: var(--text-primary);
          background: var(--bg-card-hover);
        }
      }
    }

    /* Segment Navigation Bar */
    .segment-nav-bar {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 1.5rem;
      padding: 0.5rem 1rem;
      background: rgba(102, 126, 234, 0.1);
      border-bottom: 1px solid rgba(102, 126, 234, 0.2);
      flex-shrink: 0;
      
      .nav-btn {
        color: var(--text-primary);
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        transition: all 0.2s;
        
        &:hover:not(:disabled) {
          background: var(--bg-card-hover);
          border-color: var(--border-hover);
          transform: scale(1.1);
        }
        
        &:disabled {
          opacity: 0.3;
        }
      }
      
      .segment-info {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
        
        .segment-label {
          color: var(--text-muted);
        }
        
        .segment-number {
          font-weight: 700;
          font-size: 1.25rem;
          color: var(--accent-primary);
          min-width: 2rem;
          text-align: center;
        }
        
        .segment-separator {
          color: var(--text-muted);
        }
        
        .segment-total {
          font-weight: 600;
          color: var(--text-secondary);
        }
      }
    }

    /* Video Section */
    .video-section {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #000;
      flex-shrink: 0;
      max-height: 45vh;
      
      .video-player {
        width: 100%;
        height: auto;
        max-height: 45vh;
        object-fit: contain;
      }
      
      .loading-overlay {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.9);
        gap: 1rem;
        
        p {
          color: var(--text-secondary);
          font-size: 0.9rem;
        }
      }
      
      .error-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        padding: 2rem;
        
        mat-icon {
          font-size: 3rem;
          width: 3rem;
          height: 3rem;
          color: #ef4444;
        }
        
        p {
          color: var(--text-secondary);
          text-align: center;
        }
      }
    }

    /* Info Section - Below Video */
    .info-section {
      flex: 1;
      overflow-y: auto;
      padding: 1rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    /* AI Reasoning Card */
    .reasoning-card {
      background: linear-gradient(135deg, rgba(6, 255, 165, 0.08) 0%, rgba(6, 255, 165, 0.02) 100%);
      border: 1px solid rgba(6, 255, 165, 0.2);
      border-radius: 12px;
      padding: 1rem;
      
      .card-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        
        mat-icon {
          color: #06FFA5;
          font-size: 1.25rem;
        }
        
        h3 {
          margin: 0;
          font-size: 0.9rem;
          font-weight: 600;
          color: #06FFA5;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
      }
      
      .reasoning-text {
        margin: 0;
        color: var(--text-primary);
        line-height: 1.7;
        font-size: 0.95rem;
        max-height: 150px;
        overflow-y: auto;
        padding-right: 0.5rem;
        transition: color 0.3s ease;
        
        &::-webkit-scrollbar {
          width: 4px;
        }
        
        &::-webkit-scrollbar-thumb {
          background: var(--accent-success);
          border-radius: 2px;
        }
      }
    }

    /* Metadata Section */
    .metadata-section {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      
      .metadata-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
      
      .meta-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem 0.75rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        font-size: 0.8rem;
        color: var(--text-secondary);
        transition: background 0.3s ease, border-color 0.3s ease, color 0.3s ease;
        
        mat-icon {
          font-size: 1rem;
          width: 1rem;
          height: 1rem;
          color: var(--text-muted);
        }
        
        &.public {
          background: rgba(34, 197, 94, 0.1);
          border-color: rgba(34, 197, 94, 0.3);
          color: #22c55e;
          
          mat-icon { color: #22c55e; }
        }
        
        &.private {
          background: rgba(251, 191, 36, 0.1);
          border-color: rgba(251, 191, 36, 0.3);
          color: #fbbf24;
          
          mat-icon { color: #fbbf24; }
        }
      }
      
      .tags-row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.5rem;
        
        .tags-icon {
          font-size: 1rem;
          width: 1rem;
          height: 1rem;
          color: rgba(102, 126, 234, 0.7);
        }
        
        .tag-chip {
          padding: 0.3rem 0.7rem;
          background: rgba(102, 126, 234, 0.15);
          border: 1px solid rgba(102, 126, 234, 0.3);
          border-radius: 6px;
          font-size: 0.75rem;
          color: rgba(102, 126, 234, 0.9);
          font-weight: 500;
        }
      }
    }

    /* Scrollbar styling */
    .info-section::-webkit-scrollbar {
      width: 6px;
    }
    
    .info-section::-webkit-scrollbar-track {
      background: transparent;
    }
    
    .info-section::-webkit-scrollbar-thumb {
      background: var(--scrollbar-thumb);
      border-radius: 3px;
    }

    /* Responsive */
    @media (max-width: 600px) {
      .player-header .header-info h2 {
        max-width: 200px;
      }
      
      .metadata-section .meta-chip {
        font-size: 0.75rem;
        padding: 0.3rem 0.6rem;
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

