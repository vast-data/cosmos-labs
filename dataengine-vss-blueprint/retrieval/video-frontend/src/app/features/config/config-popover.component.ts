import { Component, inject, signal, HostListener, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-config-popover',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  template: `
    @if (isVisible()) {
      <div class="backdrop" (click)="close()"></div>
    }
    <div class="config-popover" [class.visible]="isVisible()" #popoverElement (click)="$event.stopPropagation()">
      <div class="popover-header">
        <mat-icon class="header-icon">code</mat-icon>
        <span class="header-title">Backend Config</span>
        <button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      @if (loading()) {
        <div class="loading-state">
          <div class="spinner"></div>
          <span>Loading...</span>
        </div>
      }

      @if (error()) {
        <div class="error-state">
          <mat-icon>error_outline</mat-icon>
          <span>{{ error() }}</span>
        </div>
      }

      @if (yamlContent() && !loading()) {
        <div class="yaml-container">
          <pre class="yaml-code">{{ yamlContent() }}</pre>
        </div>
      }

      <div class="popover-footer">
        <button class="refresh-btn" (click)="refresh()">
          <mat-icon>refresh</mat-icon>
        </button>
      </div>
    </div>
  `,
  styles: [`
    .backdrop {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.2);
      z-index: 9997;
      cursor: pointer;
    }

    .config-popover {
      position: fixed;
      top: 80px;
      right: 20px;
      width: 450px;
      max-height: 70vh;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
      z-index: 9998;
      display: flex;
      flex-direction: column;
      opacity: 0;
      transform: translateY(-10px) scale(0.95);
      pointer-events: none;
      transition: all 0.2s ease, background 0.3s ease, border-color 0.3s ease;
      
      &.visible {
        opacity: 1;
        transform: translateY(0) scale(1);
        pointer-events: all;
      }
    }

    .popover-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1rem 1rem 0.75rem 1rem;
      background: transparent;
      
      .header-icon {
        font-size: 24px;
        width: 24px;
        height: 24px;
        color: var(--accent-primary);
      }
      
      .header-title {
        flex: 1;
        color: var(--text-primary);
        font-size: 1rem;
        font-weight: 500;
        font-family: 'Roboto Mono', monospace;
      }
      
      .close-btn {
        background: transparent;
        border: none;
        padding: 0.25rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        border-radius: 4px;
        transition: all 0.2s ease;
        
        mat-icon {
          font-size: 18px;
          width: 18px;
          height: 18px;
          color: var(--text-secondary);
        }
        
        &:hover {
          background: var(--bg-card-hover);
          
          mat-icon {
            color: var(--text-primary);
          }
        }
      }
    }

    .loading-state,
    .error-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      gap: 0.75rem;
      color: var(--text-secondary);
      font-size: 0.85rem;
      
      mat-icon {
        font-size: 32px;
        width: 32px;
        height: 32px;
        color: var(--accent-danger);
      }
    }

    .spinner {
      width: 28px;
      height: 28px;
      border: 3px solid var(--border-color);
      border-top-color: var(--accent-primary);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .yaml-container {
      flex: 1;
      overflow-y: auto;
      padding: 1rem;
      
      &::-webkit-scrollbar {
        width: 6px;
      }
      
      &::-webkit-scrollbar-track {
        background: var(--scrollbar-track);
      }
      
      &::-webkit-scrollbar-thumb {
        background: var(--scrollbar-thumb);
        border-radius: 3px;
      }
      
      &::-webkit-scrollbar-thumb:hover {
        background: var(--scrollbar-thumb-hover);
      }
    }

    .yaml-code {
      font-family: 'Roboto Mono', 'Courier New', monospace;
      font-size: 0.8rem;
      line-height: 1.6;
      color: var(--text-primary);
      margin: 0;
      white-space: pre;
      word-wrap: normal;
      overflow-x: auto;
      background: var(--bg-secondary);
      padding: 1rem;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      transition: background 0.3s ease, color 0.3s ease, border-color 0.3s ease;
      
      /* YAML syntax highlighting (manual) */
      /* Keys are turquoise */
    }

    .popover-footer {
      padding: 0.5rem;
      border-top: 1px solid var(--border-color);
      display: flex;
      justify-content: flex-end;
      transition: border-color 0.3s ease;
      
      .refresh-btn {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 0.4rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        transition: all 0.2s ease;
        
        mat-icon {
          font-size: 18px;
          width: 18px;
          height: 18px;
          color: var(--accent-primary);
        }
        
        &:hover {
          background: var(--bg-card-hover);
          border-color: var(--border-hover);
          transform: rotate(180deg);
        }
      }
    }
  `]
})
export class ConfigPopoverComponent {
  http = inject(HttpClient);
  
  isVisible = signal(false);
  loading = signal(true);
  error = signal<string | null>(null);
  yamlContent = signal<string>('');

  open() {
    this.isVisible.set(true);
    this.loadConfig();
  }

  close() {
    this.isVisible.set(false);
  }

  refresh() {
    this.loadConfig();
  }

  loadConfig() {
    this.loading.set(true);
    this.error.set(null);

    this.http.get<any>(`${environment.apiUrl}/config`).subscribe({
      next: (data) => {
        this.yamlContent.set(this.convertToYAML(data));
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err.error?.detail || 'Failed to load configuration');
        this.loading.set(false);
      }
    });
  }

  convertToYAML(obj: any, indent = 0): string {
    let yaml = '';
    const spaces = '  '.repeat(indent);

    for (const [key, value] of Object.entries(obj)) {
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        yaml += `${spaces}${key}:\n`;
        yaml += this.convertToYAML(value, indent + 1);
      } else if (Array.isArray(value)) {
        yaml += `${spaces}${key}:\n`;
        for (const item of value) {
          yaml += `${spaces}  - ${this.formatValue(item)}\n`;
        }
      } else {
        yaml += `${spaces}${key}: ${this.formatValue(value)}\n`;
      }
    }

    return yaml;
  }

  formatValue(value: any): string {
    if (value === null || value === undefined) {
      return 'null';
    }
    if (typeof value === 'string') {
      return `"${value}"`;
    }
    return String(value);
  }
}

