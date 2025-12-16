import { Component, EventEmitter, Input, Output, ViewChild, ElementRef, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { VideoSearchResult } from '../../../shared/models/video.model';
import { VideoService } from '../../../shared/services/video.service';

@Component({
  selector: 'app-video-card',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatChipsModule],
  template: `
    <mat-card class="video-card" (click)="onPlay()" 
              (mouseenter)="onHoverStart()" 
              (mouseleave)="onHoverEnd()">
      <div class="video-preview-container">
        <video #videoElement
               [src]="videoUrl"
               class="video-preview"
               [muted]="true"
               [loop]="true"
               playsinline
               preload="auto"
               (loadeddata)="onVideoLoaded()">
        </video>
        <div class="play-overlay" [class.hidden]="isPlaying">
          <mat-icon>play_circle_filled</mat-icon>
        </div>
      </div>

      <mat-card-content>
        <h3 class="video-title">{{ video.filename }}</h3>
        
        <div class="reasoning-content" [class.expanded]="isExpanded">
          <mat-icon class="reasoning-icon">psychology</mat-icon>
          <p>{{ video.reasoning_content }}</p>
        </div>
        @if (video.reasoning_content && video.reasoning_content.length > 200) {
          <button class="expand-toggle" (click)="toggleExpand($event)">
            <mat-icon>{{ isExpanded ? 'expand_less' : 'expand_more' }}</mat-icon>
            {{ isExpanded ? 'See less' : 'See more' }}
          </button>
        }

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
          <span class="metadata-item similarity-score">
            <mat-icon>star</mat-icon>
            {{ (video.similarity_score * 100).toFixed(1) }}%
          </span>
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
      position: relative;
      
      &:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
        border-color: rgba(102, 126, 234, 0.5);
      }
    }

    .video-preview-container {
      position: relative;
      width: 100%;
      height: 200px;
      background: #000;
      overflow: hidden;
    }

    .video-preview {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .play-overlay {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.4);
      transition: opacity 0.3s ease;
      pointer-events: none;
      opacity: 1;
      
      &.hidden {
        opacity: 0;
      }
      
      mat-icon {
        font-size: 4rem;
        width: 4rem;
        height: 4rem;
        color: rgba(255, 255, 255, 0.9);
        filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.5));
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
      margin-bottom: 0.5rem;
      
      .reasoning-icon {
        color: rgba(6, 255, 165, 0.8);
        font-size: 1.25rem;
        flex-shrink: 0;
      }
      
      p {
        margin: 0;
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.9rem;
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
        overflow: hidden;
        transition: all 0.3s ease;
      }
      
      &.expanded p {
        -webkit-line-clamp: unset;
        display: block;
      }
    }
    
    .expand-toggle {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      background: transparent;
      border: none;
      color: rgba(6, 255, 165, 0.8);
      font-size: 0.8rem;
      cursor: pointer;
      padding: 0.25rem 0.5rem;
      margin-bottom: 0.75rem;
      border-radius: 4px;
      transition: all 0.2s ease;
      
      mat-icon {
        font-size: 1rem;
        width: 1rem;
        height: 1rem;
      }
      
      &:hover {
        background: rgba(6, 255, 165, 0.1);
        color: rgba(6, 255, 165, 1);
      }
    }

    .video-metadata {
      display: flex;
      flex-wrap: nowrap;
      gap: 0.5rem;
      margin-bottom: 1rem;
      overflow-x: auto;
      overflow-y: hidden;
      
      /* Hide scrollbar but keep functionality */
      scrollbar-width: none;
      -ms-overflow-style: none;
      &::-webkit-scrollbar {
        display: none;
      }
      
      .metadata-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.7);
        background: rgba(255, 255, 255, 0.03);
        padding: 0.25rem 0.6rem;
        border-radius: 8px;
        white-space: nowrap;
        flex-shrink: 0;
        
        mat-icon {
          font-size: 0.95rem;
          width: 0.95rem;
          height: 0.95rem;
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
        
        &.similarity-score {
          background: rgba(102, 126, 234, 0.15);
          color: rgba(102, 126, 234, 1);
          border: 1px solid rgba(102, 126, 234, 0.4);
          font-weight: 600;
          
          mat-icon {
            color: rgba(102, 126, 234, 1);
          }
        }
      }
    }

    .tags-container {
      margin-bottom: 0;
    }

    .tags {
      ::ng-deep mat-chip {
        background: rgba(102, 126, 234, 0.1);
        color: rgba(102, 126, 234, 0.9);
        border: 1px solid rgba(102, 126, 234, 0.2);
        font-size: 0.75rem;
      }
    }

    ::ng-deep .mat-mdc-card-content {
      padding: 1rem;
      padding-bottom: 1rem !important;
    }
  `]
})
export class VideoCardComponent implements OnInit {
  private videoService = inject(VideoService);
  
  @Input({ required: true }) video!: VideoSearchResult;
  @Output() play = new EventEmitter<VideoSearchResult>();
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;

  isPlaying = false;
  isVideoLoaded = false;
  isExpanded = false;
  videoUrl: string = '';

  ngOnInit() {
    // Get authentication token and generate proper stream URL
    const token = localStorage.getItem('video_lab_token');
    if (token) {
      this.videoUrl = this.videoService.getStreamUrl(this.video.source, token);
      console.log('[VIDEO CARD] Stream URL generated for hover preview:', this.videoUrl);
    } else {
      console.error('[VIDEO CARD] No token found for video preview');
    }
  }

  onPlay() {
    this.play.emit(this.video);
  }

  toggleExpand(event: Event) {
    event.stopPropagation(); // Prevent card click
    this.isExpanded = !this.isExpanded;
  }

  onVideoLoaded() {
    this.isVideoLoaded = true;
    console.log('[VIDEO CARD] Video loaded and ready for hover preview');
  }

  async onHoverStart() {
    if (!this.videoElement?.nativeElement) {
      console.log('[VIDEO CARD] Video element not available yet');
      return;
    }

    const video = this.videoElement.nativeElement;
    console.log('[VIDEO CARD] Hover start - readyState:', video.readyState, 'isVideoLoaded:', this.isVideoLoaded);
    
    try {
      if (video.readyState >= 2) { 
        // Video has enough data to start playing
        console.log('[VIDEO CARD] Video ready, attempting play...');
        await video.play();
        this.isPlaying = true;
        console.log('[VIDEO CARD] Video playing on hover');
      } else {
        // Wait for video to be ready
        console.log('[VIDEO CARD] Video not ready, waiting for canplay event...');
        const playWhenReady = async () => {
          try {
            console.log('[VIDEO CARD] canplay event fired, attempting play...');
            await video.play();
            this.isPlaying = true;
            console.log('[VIDEO CARD] Video playing after canplay');
          } catch (err) {
            console.error('[VIDEO CARD] Play failed after canplay:', err);
          }
        };
        video.addEventListener('canplay', playWhenReady, { once: true });
      }
    } catch (err) {
      console.error('[VIDEO CARD] Play failed on hover:', err);
    }
  }

  onHoverEnd() {
    if (this.videoElement?.nativeElement) {
      const video = this.videoElement.nativeElement;
      console.log('[VIDEO CARD] Hover end - pausing and resetting video');
      video.pause();
      video.currentTime = 0;
      this.isPlaying = false;
    }
  }
}

