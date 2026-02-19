import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-search-animation',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  template: `
    <div class="search-animation-container" [class.active]="isActive" (click)="onBackdropClick()">
      <div class="animation-card" (click)="$event.stopPropagation()">
        <!-- Phase 1: Embedding -->
        <div class="phase" [class.active]="phase === 'embedding'" [class.complete]="phaseIndex > 0">
          <div class="phase-icon">
            <mat-icon>psychology</mat-icon>
          </div>
          <div class="phase-content">
            <h3>Generating Embedding</h3>
            <p>Converting query to vector using NVIDIA NIM</p>
            <div class="model-info">Model: nvidia/nv-embedqa-e5-v5 (1024 dims)</div>
            @if (phase === 'embedding') {
              <div class="loader">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
              </div>
            }
            @if (phaseIndex > 0) {
              <div class="checkmark">
                <mat-icon>check_circle</mat-icon>
              </div>
            }
          </div>
        </div>

        <!-- Phase 2: Searching -->
        <div class="phase" [class.active]="phase === 'searching'" [class.complete]="phaseIndex > 1">
          <div class="phase-icon">
            <mat-icon>search</mat-icon>
          </div>
          <div class="phase-content">
            <h3>Searching VastDB</h3>
            <p>Performing cosine similarity search on vector store</p>
            <div class="model-info">Searching through thousands of video segments...</div>
            @if (phase === 'searching') {
              <div class="vector-animation">
                <div class="vector-point" *ngFor="let i of [0,1,2,3,4,5,6,7,8]" [style.animation-delay.ms]="i * 100"></div>
              </div>
            }
            @if (phaseIndex > 1) {
              <div class="checkmark">
                <mat-icon>check_circle</mat-icon>
              </div>
            }
          </div>
        </div>

        <!-- Phase 3: Filtering -->
        <div class="phase" [class.active]="phase === 'filtering'" [class.complete]="phaseIndex > 2">
          <div class="phase-icon">
            <mat-icon>lock</mat-icon>
          </div>
          <div class="phase-content">
            <h3>Applying Permissions</h3>
            <p>Filtering results based on your access rights</p>
            <div class="model-info">Checking allowed_users, is_public...</div>
            @if (phase === 'filtering') {
              <div class="loader">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
              </div>
            }
            @if (phaseIndex > 2) {
              <div class="checkmark">
                <mat-icon>check_circle</mat-icon>
              </div>
            }
          </div>
        </div>

        <!-- Phase 4: LLM Synthesis (only shown when LLM is enabled) -->
        <div *ngIf="showLlmPhase" class="phase" [class.active]="phase === 'synthesizing'" [class.complete]="phaseIndex > 3">
          <div class="phase-icon">
            <mat-icon>auto_awesome</mat-icon>
          </div>
          <div class="phase-content">
            <h3>Generating LLM Summary</h3>
            <p>Synthesizing top results with NVIDIA AI</p>
            <div class="model-info">Model: meta/llama-3.1-8b-instruct</div>
            @if (phase === 'synthesizing') {
              <div class="loader">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
              </div>
            }
            @if (phaseIndex > 3) {
              <div class="checkmark">
                <mat-icon>check_circle</mat-icon>
              </div>
            }
          </div>
        </div>

        <!-- Phase 5: Complete -->
        @if (phase === 'complete') {
          <div class="phase active">
            <div class="phase-icon">
              <mat-icon>done_all</mat-icon>
            </div>
            <div class="phase-content">
              <h3>Search Complete!</h3>
              <p>Found {{ resultsCount }} matching videos</p>
              @if (embeddingTime > 0 && searchTime > 0) {
                <div class="timing-info">
                  <span>Embedding: {{ embeddingTime.toFixed(2) }}ms</span>
                  <span>Search: {{ searchTime.toFixed(2) }}ms</span>
                  @if (showLlmPhase && llmTime > 0) {
                    <span>LLM: {{ llmTime.toFixed(2) }}ms</span>
                  }
                </div>
              }
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .search-animation-container {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(10px);
      z-index: 9999;
      align-items: center;
      justify-content: center;
      
      &.active {
        display: flex;
      }
    }

    .animation-card {
      position: relative;
      background: rgba(26, 26, 46, 0.95);
      border: 1px solid rgba(0, 206, 209, 0.3);
      border-radius: 20px;
      padding: 2rem;
      max-width: 450px;
      width: 85%;
      box-shadow: 0 15px 45px rgba(0, 0, 0, 0.5),
                  0 0 80px rgba(0, 206, 209, 0.2);
    }

    .phase {
      display: flex;
      align-items: flex-start;
      gap: 1.25rem;
      padding: 1.25rem;
      margin-bottom: 0.75rem;
      border-radius: 14px;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      opacity: 0.3;
      transition: all 0.3s ease;
      
      &.active {
        opacity: 1;
        background: var(--bg-card-hover);
        border: 1px solid var(--accent-primary);
      }
      
      &.complete {
        opacity: 0.6;
        background: var(--bg-card);
        border: 1px solid var(--accent-success);
      }
    }

    .phase-icon {
      min-width: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      mat-icon {
        font-size: 2.5rem;
        width: 2.5rem;
        height: 2.5rem;
        color: rgba(0, 206, 209, 0.85);
        transition: all 0.3s ease;
      }
      
      .phase.active & mat-icon {
        color: #00CED1;
        filter: drop-shadow(0 0 8px rgba(0, 206, 209, 0.6));
      }
      
      .phase.complete & mat-icon {
        color: #06ffa5;
      }
    }

    .phase-content {
      flex: 1;
      
      h3 {
        color: var(--text-primary);
        font-size: 1.1rem;
        margin: 0 0 0.4rem 0;
      }
      
      p {
        color: var(--text-secondary);
        margin: 0 0 0.4rem 0;
        font-size: 0.9rem;
      }
      
      .model-info {
        font-size: 0.8rem;
        color: rgba(0, 206, 209, 0.75);
        font-family: 'Courier New', monospace;
        margin-top: 0.4rem;
      }
      
      .timing-info {
        display: flex;
        gap: 0.75rem;
        margin-top: 0.5rem;
        font-size: 0.8rem;
        color: rgba(6, 255, 165, 0.8);
        
        span {
          background: rgba(6, 255, 165, 0.1);
          padding: 0.2rem 0.6rem;
          border-radius: 6px;
        }
      }
    }

    .loader {
      display: flex;
      gap: 0.5rem;
      margin-top: 0.75rem;
      
      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #00CED1;
        animation: bounce 1s infinite;
        
        &:nth-child(2) {
          animation-delay: 0.2s;
        }
        
        &:nth-child(3) {
          animation-delay: 0.4s;
        }
      }
    }

    @keyframes bounce {
      0%, 100% {
        transform: translateY(0);
      }
      50% {
        transform: translateY(-8px);
      }
    }

    .vector-animation {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.4rem;
      margin-top: 0.75rem;
      
      .vector-point {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #00CED1 0%, #008B8B 100%);
        border-radius: 6px;
        animation: pulse 1.5s infinite;
      }
    }

    @keyframes pulse {
      0%, 100% {
        opacity: 0.3;
        transform: scale(0.9);
      }
      50% {
        opacity: 1;
        transform: scale(1.1);
      }
    }

    .checkmark {
      margin-top: 0.5rem;
      animation: scaleIn 0.3s ease-out;
      display: flex;
      align-items: center;
      
      mat-icon {
        font-size: 1.5rem;
        width: 1.5rem;
        height: 1.5rem;
        color: #06ffa5;
      }
    }

    @keyframes scaleIn {
      from {
        transform: scale(0);
      }
      to {
        transform: scale(1);
      }
    }
  `]
})
export class SearchAnimationComponent {
  @Input() phase: 'idle' | 'embedding' | 'searching' | 'filtering' | 'synthesizing' | 'complete' = 'idle';
  @Input() embeddingTime: number = 0;
  @Input() searchTime: number = 0;
  @Input() llmTime: number = 0;
  @Input() resultsCount: number = 0;
  @Input() showLlmPhase: boolean = false;
  @Output() close = new EventEmitter<void>();

  get isActive(): boolean {
    return this.phase !== 'idle';
  }

  get phaseIndex(): number {
    const phases = ['embedding', 'searching', 'filtering', 'synthesizing', 'complete'];
    return phases.indexOf(this.phase);
  }

  onClose() {
    this.close.emit();
  }

  onBackdropClick() {
    // Only allow closing when search is complete
    if (this.phase === 'complete') {
      this.close.emit();
    }
  }
}

