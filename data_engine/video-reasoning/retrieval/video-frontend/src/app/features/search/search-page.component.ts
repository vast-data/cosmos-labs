import { Component, inject, signal, OnDestroy, OnInit, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { SearchBarComponent } from './components/search-bar.component';
import { VideoCardComponent } from './components/video-card.component';
import { SearchAnimationComponent } from './components/search-animation.component';
import { LLMSynthesisComponent } from './components/llm-synthesis.component';
import { SearchService } from './services/search.service';
import { SearchRequest, VideoSearchResult } from '../../shared/models/video.model';
import { VideoPlayerComponent } from '../player/video-player.component';
import { UploadDialogComponent } from '../upload/upload-dialog.component';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { AuthService } from '../auth/services/auth.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-search-page',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    SearchBarComponent,
    VideoCardComponent,
    SearchAnimationComponent,
    LLMSynthesisComponent
  ],
  template: `
    <div class="search-container">
      <div class="search-header">
        <button mat-raised-button 
                color="accent" 
                (click)="openUpload()" 
                [disabled]="isOpeningDialog()"
                class="upload-button">
          <mat-icon>{{ isOpeningDialog() ? 'hourglass_empty' : 'cloud_upload' }}</mat-icon>
          {{ isOpeningDialog() ? 'Opening...' : 'Upload Video' }}
        </button>
      </div>

      <app-search-bar (search)="onSearch($event)"></app-search-bar>

      @if (searchService.state().error) {
        <div class="error-message">
          <mat-icon>error_outline</mat-icon>
          <span>{{ searchService.state().error }}</span>
        </div>
      }

      @if (!hasSearched() && !searchService.state().loading) {
        <div class="empty-state">
          <img src="assets/vast_logo.svg" alt="VAST" class="vast-logo-glow">
          <h2>Ready to search</h2>
          <p>Enter a natural language query to find videos with AI-powered semantic search</p>
          <div class="examples">
            <h3>Example queries:</h3>
            <ul>
              @for (example of exampleQueries(); track example) {
                <li><mat-icon>search</mat-icon> "{{ example }}"</li>
              }
            </ul>
          </div>
        </div>
      }

      @if (searchService.state().results.length > 0) {
        <div class="results-header">
          <h2>Search Results</h2>
          <div class="results-info">
            <span>Found {{ searchService.state().results.length }} videos</span>
            @if (searchService.state().permissionFiltered > 0) {
              <span class="filtered-info">
                ({{ searchService.state().permissionFiltered }} filtered by permissions)
              </span>
            }
            <span class="timing-info">
              Embedding: {{ searchService.state().embeddingTimeMs.toFixed(0) }}ms | 
              Search: {{ searchService.state().searchTimeMs.toFixed(0) }}ms
            </span>
          </div>
        </div>

        <!-- LLM Synthesis (if available) -->
        @if (searchService.state().llmSynthesis) {
          <app-llm-synthesis [synthesis]="searchService.state().llmSynthesis"></app-llm-synthesis>
        }

        <div class="results-grid">
          @for (video of searchService.state().results; track video.source) {
            <app-video-card [video]="video" (play)="playVideo($event)"></app-video-card>
          }
        </div>
      }

      @if (hasSearched() && searchService.state().results.length === 0 && !searchService.state().loading) {
        <div class="no-results">
          <img src="assets/vast_logo.svg" alt="VAST" class="vast-logo-glow">
          <h2>No videos found</h2>
          <p>Try a different query or check your filters</p>
        </div>
      }
    </div>

    <app-search-animation
      [phase]="searchService.state().animationPhase"
      [embeddingTime]="searchService.state().embeddingTimeMs"
      [searchTime]="searchService.state().searchTimeMs"
      [llmTime]="searchService.state().llmTimeMs"
      [resultsCount]="searchService.state().results.length"
      [showLlmPhase]="searchService.state().llmSynthesis !== null"
      (close)="closeAnimation()">
    </app-search-animation>
  `,
  styles: [`
    .search-container {
      padding: 2rem;
      max-width: 1400px;
      margin: 0 auto;
      min-height: 100vh;
    }
    
    .search-header {
      display: flex;
      justify-content: flex-end;
      margin-bottom: 2rem;
      
      .upload-button {
        background: linear-gradient(135deg, #0047AB 0%, #002766 100%) !important;
        color: white !important;
        font-weight: 500;
        border-radius: 4px !important;
        padding: 0 1.5rem !important;
        cursor: pointer !important;
        transition: all 0.2s ease;
        
        * {
          cursor: pointer !important;
        }
        
        &:hover {
          box-shadow: 0 4px 12px rgba(0, 71, 171, 0.6);
        }
      }
    }

    .error-message {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.3);
      border-radius: 12px;
      padding: 1rem;
      color: #fca5a5;
      margin-bottom: 2rem;
      
      mat-icon {
        color: #ef4444;
      }
    }

    .empty-state {
      text-align: center;
      padding: 4rem 2rem;
      background: rgba(255, 255, 255, 0.02);
      border: 1px dashed rgba(255, 255, 255, 0.2);
      border-radius: 20px;
      
      .vast-logo-glow {
        height: 30px;
        width: auto;
        margin-bottom: 2rem;
        filter: drop-shadow(0 0 15px rgba(0, 217, 255, 0.7));
        animation: glow-pulse 1.2s ease-in-out infinite;
      }
      
      h2 {
        color: #fff;
        font-size: 2rem;
        margin-bottom: 0.5rem;
      }
      
      p {
        color: rgba(255, 255, 255, 0.7);
        font-size: 1.1rem;
        margin-bottom: 2rem;
      }
      
      .examples {
        text-align: left;
        max-width: 600px;
        margin: 0 auto;
        background: rgba(0, 71, 171, 0.08);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(0, 71, 171, 0.2);
        
        h3 {
          color: rgba(0, 217, 255, 0.9);
          margin-bottom: 0.75rem;
          font-size: 1rem;
        }
        
        ul {
          list-style: none;
          padding: 0;
          
          li {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: rgba(255, 255, 255, 0.85);
            padding: 0.5rem 0;
            
            mat-icon {
              color: #00d9ff;
              font-size: 1.25rem;
              width: 1.25rem;
              height: 1.25rem;
              flex-shrink: 0;
            }
          }
        }
      }
    }
    
    @keyframes glow-pulse {
      0%, 100% {
        filter: drop-shadow(0 0 15px rgba(0, 217, 255, 0.7));
        opacity: 1;
        transform: scale(1);
      }
      50% {
        filter: drop-shadow(0 0 40px rgba(0, 217, 255, 1));
        opacity: 0.7;
        transform: scale(1.05);
      }
    }

    .results-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      
      h2 {
        color: #fff;
        font-size: 1.5rem;
        margin: 0;
      }
      
      .results-info {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.25rem;
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.7);
        
        .filtered-info {
          color: rgba(255, 193, 7, 0.8);
        }
        
        .timing-info {
          font-family: 'Courier New', monospace;
          color: rgba(6, 255, 165, 0.7);
        }
      }
    }

    .results-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
      gap: 1.5rem;
      animation: fadeIn 0.5s ease-out;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .no-results {
      text-align: center;
      padding: 4rem 2rem;
      
      .vast-logo-glow {
        height: 30px;
        width: auto;
        margin-bottom: 2rem;
        filter: drop-shadow(0 0 15px rgba(0, 217, 255, 0.7));
        animation: glow-pulse 1.2s ease-in-out infinite;
      }
      
      h2 {
        color: #fff;
        font-size: 1.75rem;
        margin-bottom: 0.5rem;
      }
      
      p {
        color: rgba(255, 255, 255, 0.6);
      }
    }
  `]
})
export class SearchPageComponent implements OnInit, OnDestroy {
  searchService = inject(SearchService);
  dialog = inject(MatDialog);
  authService = inject(AuthService);
  http = inject(HttpClient);
  
  hasSearched = signal(false);
  isOpeningDialog = signal(false);
  exampleQueries = signal<string[]>([]);
  
  // Store dialog references to close them on logout
  private uploadDialogRef: MatDialogRef<UploadDialogComponent> | null = null;
  
  ngOnInit() {
    this.loadExampleQueries();
  }

  loadExampleQueries() {
    this.http.get<any>(`${environment.apiUrl}/frontend/search-suggestions`).subscribe({
      next: (config) => {
        if (config.placeholder_examples && config.placeholder_examples.length > 0) {
          this.exampleQueries.set(config.placeholder_examples);
        }
      },
      error: (err) => {
        console.error('Failed to load example queries, using defaults', err);
        // Set default fallback examples
        this.exampleQueries.set([
          'suspicious person near fence',
          'unattended bag',
          'vehicle running red light'
        ]);
      }
    });
  }
  
  constructor() {
    // Watch auth status to close dialogs on logout
    effect(() => {
      const status = this.authService.status();
      if (status === 'pending' && !this.authService.token()) {
        // User logged out - close all dialogs
        if (this.uploadDialogRef) {
          this.uploadDialogRef.close();
          this.uploadDialogRef = null;
        }
        this.dialog.closeAll();
      }
    });
  }
  
  ngOnDestroy() {
    // Clean up any open dialogs
    if (this.uploadDialogRef) {
      this.uploadDialogRef.close();
    }
  }

  onSearch(request: SearchRequest) {
    this.hasSearched.set(true);
    this.searchService.search(request);
  }

  closeAnimation() {
    this.searchService.closeAnimation();
  }

  playVideo(video: VideoSearchResult) {
    this.dialog.open(VideoPlayerComponent, {
      data: { video },
      width: '90vw',
      maxWidth: '1200px',
      height: '90vh',
      panelClass: 'video-player-dialog'
    });
  }

  openUpload() {
    // Prevent multiple clicks
    if (this.isOpeningDialog()) {
      return;
    }
    
    this.isOpeningDialog.set(true);
    
    // Use setTimeout to ensure proper initialization
    setTimeout(() => {
      this.uploadDialogRef = this.dialog.open(UploadDialogComponent, {
        width: '600px',
        maxWidth: '95vw',
        panelClass: 'upload-dialog',
        disableClose: false,
        autoFocus: true,
        restoreFocus: true
      });
      
      // Reset loading state immediately after dialog opens
      this.isOpeningDialog.set(false);
      
      // Clean up reference when dialog closes
      this.uploadDialogRef.afterClosed().subscribe(() => {
        this.uploadDialogRef = null;
      });
    }, 0);
  }
}


