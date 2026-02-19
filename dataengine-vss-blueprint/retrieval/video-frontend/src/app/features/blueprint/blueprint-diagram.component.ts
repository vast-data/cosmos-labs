import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';

@Component({
  selector: 'app-blueprint-diagram',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatMenuModule],
  template: `
    <div class="blueprint-page">
      <div class="page-header">
        <mat-icon class="header-icon">architecture</mat-icon>
        <h2>VAST DataEngine - Video Search & Summarization Blueprint</h2>
      </div>

      <div class="page-content">
        <div class="blueprint-container">
          <!-- VAST Platform Header -->
          <div class="platform-header">
            <div class="platform-badge">
              <mat-icon>cloud</mat-icon>
              <span>Blueprint Breakdown</span>
            </div>
            <div class="platform-value">
              <mat-icon>flash_on</mat-icon>
              <span class="platform-value-text">Event-Based Serverless Video Processing: Upload → Segmentation → AI Analysis → Vector Search</span>
            </div>
          </div>

          <!-- Ingestion Pipeline - VLM Flow -->
          <div class="pipeline-section">
            <div class="section-title">
              <mat-icon>download</mat-icon>
              <span>Ingestion Pipeline - VLM Flow (Event-Based Serverless)</span>
            </div>
            <div class="section-subtitle">
              <mat-icon>info</mat-icon>
              <span>Real-time video processing: Video Upload → Segmentation → VLM Reasoning → Embedding → Vector Storage</span>
            </div>
            
            <div class="pipeline-flow">
              <!-- Video Upload Sources -->
              <div class="component-box storage">
                <div class="component-icon">
                  <mat-icon>video_library</mat-icon>
                </div>
                <div class="component-title">Video Sources</div>
                <div class="component-desc">Upload / Streaming<br/>YouTube / S3 Batch</div>
                <div class="component-badge">S3 Compatible</div>
              </div>

              <div class="arrow-right"></div>

              <!-- VAST S3 Storage -->
              <div class="component-box storage">
                <div class="component-icon">
                  <mat-icon>storage</mat-icon>
                </div>
                <div class="component-title">VAST S3</div>
                <div class="component-desc">Object Storage<br/>video-chunks</div>
                <div class="component-badge">S3 Compatible</div>
              </div>

              <div class="arrow-right"></div>

              <!-- VAST Event Broker -->
              <div class="component-box trigger">
                <div class="component-icon">
                  <mat-icon>hub</mat-icon>
                </div>
                <div class="component-title">VAST Event Broker</div>
                <div class="component-desc">Event Routing<br/>& Distribution</div>
                <div class="component-badge">Event Broker</div>
              </div>

              <div class="arrow-right"></div>

              <!-- S3 Event Trigger -->
              <div class="component-box trigger">
                <div class="component-icon">
                  <mat-icon>bolt</mat-icon>
                </div>
                <div class="component-title">S3 Event Trigger</div>
                <div class="component-desc">Auto-trigger on<br/>video upload</div>
                <div class="component-badge">DataEngine</div>
              </div>

              <div class="arrow-right"></div>

              <!-- Video Segmenter -->
              <div class="component-box function">
                <div class="component-icon">
                  <mat-icon>content_cut</mat-icon>
                </div>
                <div class="component-title">Video Segmenter</div>
                <div class="component-desc">Split into Segments<br/>FFmpeg Processing</div>
                <div class="component-badge">Serverless</div>
              </div>

              <div class="arrow-right"></div>

              <!-- Segments S3 -->
              <div class="component-box storage">
                <div class="component-icon">
                  <mat-icon>storage</mat-icon>
                </div>
                <div class="component-title">VAST S3</div>
                <div class="component-desc">Segments Storage<br/>video-chunks-segments</div>
                <div class="component-badge">S3 Compatible</div>
              </div>

              <div class="arrow-right"></div>

              <!-- S3 Event Trigger (Segments) -->
              <div class="component-box trigger">
                <div class="component-icon">
                  <mat-icon>bolt</mat-icon>
                </div>
                <div class="component-title">S3 Event Trigger</div>
                <div class="component-desc">Auto-trigger on<br/>segment creation</div>
                <div class="component-badge">DataEngine</div>
              </div>

              <div class="arrow-right"></div>

              <!-- Video Reasoner -->
              <div class="component-box function">
                <div class="component-icon">
                  <mat-icon>psychology</mat-icon>
                </div>
                <div class="component-title">Video Reasoner</div>
                <div class="component-desc">NVIDIA Cosmos VLM<br/>Video Understanding</div>
                <div class="component-badge">NVIDIA NIM</div>
              </div>

              <div class="arrow-right"></div>

              <!-- Video Embedder -->
              <div class="component-box function">
                <div class="component-icon">
                  <mat-icon>transform</mat-icon>
                </div>
                <div class="component-title">Video Embedder</div>
                <div class="component-desc">NVIDIA NIM<br/>1024-dim vectors</div>
                <div class="component-badge">NVIDIA NIM</div>
              </div>

              <div class="arrow-right"></div>

              <!-- VastDB Writer -->
              <div class="component-box function">
                <div class="component-icon">
                  <mat-icon>save</mat-icon>
                </div>
                <div class="component-title">VastDB Writer</div>
                <div class="component-desc">Ingest to VastDB<br/>Vectors + Metadata</div>
                <div class="component-badge">Serverless</div>
              </div>

              <div class="arrow-right"></div>

              <!-- VastDB -->
              <div class="component-box database">
                <div class="component-icon">
                  <mat-icon>storage</mat-icon>
                </div>
                <div class="component-title">VastDB</div>
                <div class="component-desc">Vector Database<br/>Structured + Vectors</div>
                <div class="component-badge">Lakehouse</div>
              </div>
            </div>
          </div>

          <!-- Retrieval & Search Pipeline -->
          <div class="pipeline-section">
            <div class="section-title">
              <mat-icon>search</mat-icon>
              <span>Retrieval & Search Pipeline</span>
            </div>
            <div class="section-subtitle">
              <mat-icon>info</mat-icon>
              <span>Hybrid search: Text Query → Embedding → Vector Similarity + Metadata Filters → LLM Synthesis</span>
            </div>
            
            <div class="pipeline-flow">
              <!-- Angular Frontend -->
              <div class="component-box dashboard">
                <div class="component-icon">
                  <mat-icon>dashboard</mat-icon>
                </div>
                <div class="component-title">Angular Frontend</div>
                <div class="component-desc">Video Search UI<br/>Material Design</div>
                <div class="component-badge">Material UI</div>
              </div>

              <div class="arrow-bidirectional"></div>

              <!-- FastAPI Backend -->
              <div class="component-box backend">
                <div class="component-icon">
                  <mat-icon>api</mat-icon>
                </div>
                <div class="component-title">FastAPI Backend</div>
                <div class="component-desc">REST API<br/>Search & Auth</div>
                <div class="component-badge">Python</div>
              </div>

              <div class="arrow-bidirectional"></div>

              <!-- Text Embedding -->
              <div class="component-box function">
                <div class="component-icon">
                  <mat-icon>psychology</mat-icon>
                </div>
                <div class="component-title">Text Embedding</div>
                <div class="component-desc">NVIDIA NIM<br/>Query → Vector</div>
                <div class="component-badge">NVIDIA NIM</div>
              </div>

              <div class="arrow-right"></div>

              <!-- Hybrid Search -->
              <div class="component-box search">
                <div class="component-icon">
                  <mat-icon>merge_type</mat-icon>
                </div>
                <div class="component-title">Hybrid Search</div>
                <div class="component-desc">Vector Similarity<br/>+ Metadata Filters</div>
                <div class="component-badge">ADBC Native</div>
              </div>

              <div class="arrow-right"></div>

              <!-- VastDB Query -->
              <div class="component-box database">
                <div class="component-icon">
                  <mat-icon>storage</mat-icon>
                </div>
                <div class="component-title">VastDB Query</div>
                <div class="component-desc">Cosine Distance<br/>ADBC Native</div>
                <div class="component-badge">Vector Search</div>
              </div>

              <div class="arrow-right"></div>

              <!-- LLM Synthesis -->
              <div class="component-box analyzer">
                <div class="component-icon">
                  <mat-icon>auto_awesome</mat-icon>
                </div>
                <div class="component-title">LLM Synthesis</div>
                <div class="component-desc">NVIDIA LLM<br/>Result Summarization</div>
                <div class="component-badge">NVIDIA NIM</div>
              </div>

              <div class="arrow-right"></div>

              <!-- Results -->
              <div class="component-box dashboard">
                <div class="component-icon">
                  <mat-icon>video_library</mat-icon>
                </div>
                <div class="component-title">Video Results</div>
                <div class="component-desc">Segments + Metadata<br/>AI Summaries</div>
                <div class="component-badge">Material UI</div>
              </div>
            </div>
          </div>

          <!-- Key Capabilities -->
          <div class="capabilities-section">
            <div class="section-title">
              <mat-icon>star</mat-icon>
              <span>Key Capabilities Of the Blueprint</span>
            </div>
            
            <div class="capabilities-grid">
              <div class="capability-item">
                <mat-icon>cloud</mat-icon>
                <span>VAST S3 Object Storage</span>
              </div>
              <div class="capability-item">
                <mat-icon>database</mat-icon>
                <span>VastDB Vector Database</span>
              </div>
              <div class="capability-item">
                <mat-icon>psychology</mat-icon>
                <span>NVIDIA Cosmos VLM</span>
              </div>
              <div class="capability-item">
                <mat-icon>psychology</mat-icon>
                <span>NVIDIA NIM Embeddings</span>
              </div>
              <div class="capability-item">
                <mat-icon>auto_awesome</mat-icon>
                <span>NVIDIA LLM Synthesis</span>
              </div>
              <div class="capability-item">
                <mat-icon>bolt</mat-icon>
                <span>DataEngine Serverless</span>
              </div>
              <div class="capability-item">
                <mat-icon>schedule</mat-icon>
                <span>S3 Event Triggers</span>
              </div>
              <div class="capability-item">
                <mat-icon>functions</mat-icon>
                <span>Serverless Functions</span>
              </div>
              <div class="capability-item">
                <mat-icon>search</mat-icon>
                <span>ADBC Vector Similarity</span>
              </div>
              <div class="capability-item">
                <mat-icon>merge_type</mat-icon>
                <span>Hybrid Search (Vector + Metadata)</span>
              </div>
              <div class="capability-item">
                <mat-icon>filter_list</mat-icon>
                <span>Dynamic Metadata Filters</span>
              </div>
              <div class="capability-item">
                <mat-icon>schedule</mat-icon>
                <span>Time-Based Filtering</span>
              </div>
              <div class="capability-item">
                <mat-icon>video_settings</mat-icon>
                <span>Video Streaming Service</span>
              </div>
              <div class="capability-item">
                <mat-icon>sync</mat-icon>
                <span>S3 Batch Video Sync</span>
              </div>
              <div class="capability-item">
                <mat-icon>security</mat-icon>
                <span>User Authentication</span>
              </div>
              <div class="capability-item">
                <mat-icon>tune</mat-icon>
                <span>Configurable VLM Prompts</span>
              </div>
              <div class="capability-item">
                <mat-icon>dashboard</mat-icon>
                <span>Real-time Video Search</span>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  `,
  styles: [`
    .blueprint-page {
      width: 100vw;
      min-height: 100vh;
      background: var(--bg-primary);
      color: var(--text-primary);
      display: flex;
      flex-direction: column;
      transition: background 0.3s ease, color 0.3s ease;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      overflow-y: auto;
      
      /* Subtle background glow effect */
      &::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 20% 30%, rgba(115, 200, 253, 0.03) 0%, transparent 50%),
                    radial-gradient(circle at 80% 70%, rgba(115, 200, 253, 0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
      }
    }

    .page-header {
      display: flex;
      align-items: center;
      gap: 0.646875rem;
      padding: 1.29375rem 1.725rem;
      border-bottom: 1px solid var(--border-color);
      transition: all 0.3s ease;
      background: var(--bg-toolbar);
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

      .header-icon {
        font-size: 24.15px;
        width: 24.15px;
        height: 24.15px;
        color: var(--accent-primary);
        filter: drop-shadow(0 0 8px rgba(115, 200, 253, 0.4));
        transition: filter 0.3s ease;
      }

      h2 {
        flex: 1;
        margin: 0;
        font-size: 1.6171875rem;
        font-weight: 600;
        color: var(--text-primary);
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
      }
    }

    .page-content {
      flex: 1;
      overflow-y: auto;
      padding: 1.725rem;
      position: relative;
      z-index: 1;
    }

    .blueprint-container {
      display: flex;
      flex-direction: column;
      gap: 1.725rem;
      animation: fadeInUp 0.6s ease-out;
    }

    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .platform-header {
      text-align: center;
      padding: 0.905625rem;
      background: var(--bg-secondary);
      border-radius: 7.245px;
      border: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      gap: 0.60375rem;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 0 20px rgba(115, 200, 253, 0.1);
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12), 0 0 30px rgba(115, 200, 253, 0.15);
        transform: translateY(-2px);
      }

      .platform-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4528125rem;
        font-size: 0.943359375rem;
        font-weight: 600;
        color: var(--text-primary);

        mat-icon {
          font-size: 24.15px;
          width: 24.15px;
          height: 24.15px;
          color: var(--accent-primary);
          filter: drop-shadow(0 0 6px rgba(115, 200, 253, 0.3));
        }
      }

      .platform-value {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.4528125rem;
        font-size: 0.7546875rem;
        font-weight: 500;
        color: var(--text-secondary);
        padding: 0.4528125rem 0.905625rem;
        background: var(--bg-card);
        border-radius: 4.83px;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;

        &:hover {
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1), 0 0 15px rgba(115, 200, 253, 0.2);
        }

        mat-icon {
          font-size: 18.1125px;
          width: 18.1125px;
          height: 18.1125px;
          color: var(--accent-primary);
        }

        .platform-value-text {
          font-size: 1.13203125rem;
        }
      }
    }

    .pipeline-section {
      background: var(--bg-secondary);
      border-radius: 7.245px;
      padding: 0.905625rem;
      border: 1px solid var(--border-color);
      transition: all 0.3s ease;
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08), 0 0 15px rgba(115, 200, 253, 0.08);

      &:hover {
        box-shadow: 0 5px 14px rgba(0, 0, 0, 0.12), 0 0 25px rgba(115, 200, 253, 0.12);
        transform: translateY(-1px);
      }

      .section-title {
        display: flex;
        align-items: center;
        gap: 0.4528125rem;
        margin-bottom: 0.4528125rem;
        font-size: 0.83015625rem;
        font-weight: 600;
        color: var(--text-primary);

        mat-icon {
          font-size: 18.1125px;
          width: 18.1125px;
          height: 18.1125px;
          color: var(--accent-primary);
          filter: drop-shadow(0 0 5px rgba(115, 200, 253, 0.3));
        }
      }

      .section-subtitle {
        display: flex;
        align-items: center;
        gap: 0.301875rem;
        margin-bottom: 0.905625rem;
        font-size: 0.67921875rem;
        font-weight: 400;
        color: var(--text-secondary);
        font-style: italic;
        padding: 0.301875rem 0.60375rem;
        background: var(--bg-card);
        border-radius: 3.6225px;
        border-left: 2px solid var(--border-color);

        mat-icon {
          font-size: 13.584375px;
          width: 13.584375px;
          height: 13.584375px;
          color: var(--accent-primary);
        }
      }
    }

    .pipeline-flow {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.8625rem;
      justify-content: center;
    }

    .component-box {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 7.245px;
      padding: 0.7546875rem;
      min-width: 84.525px;
      text-align: center;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06), 0 0 10px rgba(115, 200, 253, 0.05);

      &:hover {
        transform: translateY(-2.415px) scale(1.02);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12), 0 0 30px rgba(115, 200, 253, 0.25);
        border-color: rgba(115, 200, 253, 0.4);
        background: var(--bg-card-hover);
      }

      &.storage,
      &.trigger,
      &.function,
      &.database,
      &.analyzer,
      &.search,
      &.dashboard,
      &.backend {
        border-color: var(--border-color);
        background: var(--bg-card);
      }

      .component-icon {
        margin-bottom: 0.4528125rem;
        transition: filter 0.3s ease;

        mat-icon {
          font-size: 30.1875px;
          width: 30.1875px;
          height: 30.1875px;
          color: var(--accent-primary);
          filter: drop-shadow(0 0 4px rgba(115, 200, 253, 0.2));
          transition: filter 0.3s ease;
        }
      }

      &:hover .component-icon mat-icon {
        filter: drop-shadow(0 0 10px rgba(115, 200, 253, 0.5));
      }

      .component-title {
        font-weight: 600;
        font-size: 0.716953125rem;
        color: var(--text-primary);
        margin-bottom: 0.301875rem;
        line-height: 1.3;
      }

      .component-desc {
        font-size: 0.60375rem;
        color: var(--text-secondary);
        line-height: 1.4;
        margin-bottom: 0.4528125rem;
      }

      .component-badge {
        display: inline-block;
        padding: 0.1509375rem 0.4528125rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 9.66px;
        font-size: 0.52828125rem;
        color: var(--text-secondary);
        font-weight: 500;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
      }

      &:hover .component-badge {
        box-shadow: 0 2px 6px rgba(115, 200, 253, 0.2);
        border-color: rgba(115, 200, 253, 0.3);
      }
    }

    .arrow-right {
      width: 24.15px;
      height: 1.2075px;
      background: linear-gradient(90deg, var(--border-color), rgba(115, 200, 253, 0.3));
      position: relative;
      flex-shrink: 0;
      box-shadow: 0 0 4px rgba(115, 200, 253, 0.2);
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 0 8px rgba(115, 200, 253, 0.4);
        background: linear-gradient(90deg, rgba(115, 200, 253, 0.4), rgba(115, 200, 253, 0.6));
      }

      &::after {
        content: '';
        position: absolute;
        right: -3.6225px;
        top: -2.415px;
        width: 0;
        height: 0;
        border-left: 4.83px solid var(--border-color);
        border-top: 3.01875px solid transparent;
        border-bottom: 3.01875px solid transparent;
        filter: drop-shadow(0 0 3px rgba(115, 200, 253, 0.3));
        transition: filter 0.3s ease;
      }

      &:hover::after {
        border-left-color: rgba(115, 200, 253, 0.6);
        filter: drop-shadow(0 0 6px rgba(115, 200, 253, 0.5));
      }
    }

    .arrow-bidirectional {
      width: 24.15px;
      height: 1.2075px;
      background: linear-gradient(90deg, rgba(115, 200, 253, 0.3), var(--border-color), rgba(115, 200, 253, 0.3));
      position: relative;
      flex-shrink: 0;
      box-shadow: 0 0 4px rgba(115, 200, 253, 0.2);
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 0 8px rgba(115, 200, 253, 0.4);
        background: linear-gradient(90deg, rgba(115, 200, 253, 0.5), rgba(115, 200, 253, 0.4), rgba(115, 200, 253, 0.5));
      }

      &::before {
        content: '';
        position: absolute;
        left: -3.6225px;
        top: -2.415px;
        width: 0;
        height: 0;
        border-right: 4.83px solid var(--border-color);
        border-top: 3.01875px solid transparent;
        border-bottom: 3.01875px solid transparent;
        filter: drop-shadow(0 0 3px rgba(115, 200, 253, 0.3));
        transition: filter 0.3s ease;
      }

      &::after {
        content: '';
        position: absolute;
        right: -3.6225px;
        top: -2.415px;
        width: 0;
        height: 0;
        border-left: 4.83px solid var(--border-color);
        border-top: 3.01875px solid transparent;
        border-bottom: 3.01875px solid transparent;
        filter: drop-shadow(0 0 3px rgba(115, 200, 253, 0.3));
        transition: filter 0.3s ease;
      }

      &:hover::before,
      &:hover::after {
        border-color: rgba(115, 200, 253, 0.6);
        filter: drop-shadow(0 0 6px rgba(115, 200, 253, 0.5));
      }
    }

    .capabilities-section {
      background: var(--bg-secondary);
      border-radius: 7.245px;
      padding: 0.905625rem;
      border: 1px solid var(--border-color);
      transition: all 0.3s ease;
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08), 0 0 15px rgba(115, 200, 253, 0.08);

      &:hover {
        box-shadow: 0 5px 14px rgba(0, 0, 0, 0.12), 0 0 25px rgba(115, 200, 253, 0.12);
        transform: translateY(-1px);
      }

      .section-title {
        display: flex;
        align-items: center;
        gap: 0.4528125rem;
        margin-bottom: 0.905625rem;
        font-size: 0.83015625rem;
        font-weight: 600;
        color: var(--text-primary);

        mat-icon {
          font-size: 18.1125px;
          width: 18.1125px;
          height: 18.1125px;
          color: var(--accent-primary);
          filter: drop-shadow(0 0 5px rgba(115, 200, 253, 0.3));
        }
      }
    }

    .capabilities-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120.75px, 1fr));
      gap: 0.60375rem;

      .capability-item {
        display: flex;
        align-items: center;
        gap: 0.4528125rem;
        padding: 0.4528125rem 0.60375rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 4.83px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05), 0 0 8px rgba(115, 200, 253, 0.05);

        &:hover {
          background: var(--bg-card-hover);
          border-color: rgba(115, 200, 253, 0.4);
          transform: translateX(2.415px) scale(1.02);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1), 0 0 20px rgba(115, 200, 253, 0.2);
        }

        mat-icon {
          color: var(--accent-primary);
          font-size: 15.09375px;
          width: 15.09375px;
          height: 15.09375px;
          filter: drop-shadow(0 0 3px rgba(115, 200, 253, 0.2));
          transition: filter 0.3s ease;
        }

        &:hover mat-icon {
          filter: drop-shadow(0 0 6px rgba(115, 200, 253, 0.4));
        }

        span {
          color: var(--text-primary);
          font-size: 0.67921875rem;
          font-weight: 500;
        }
      }
    }

    /* Responsive adjustments */
    @media (max-width: 1200px) {
      .pipeline-flow {
        flex-direction: column;
        
        .arrow-right,
        .arrow-bidirectional {
          width: 1.725px;
          height: 34.5px;
          transform: rotate(90deg);
        }
      }
    }
  `]
})
export class BlueprintDiagramComponent {
  // Component for full-screen blueprint page
}

