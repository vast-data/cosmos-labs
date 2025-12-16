import { Component, inject, signal } from '@angular/core';
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
    <div class="config-popover" [class.visible]="isVisible()">
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
    .config-popover {
      position: fixed;
      top: 80px;
      right: 20px;
      width: 450px;
      max-height: 70vh;
      background: rgba(15, 15, 30, 0.98);
      border: 1px solid rgba(0, 71, 171, 0.4);
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5),
                  0 0 0 1px rgba(0, 206, 209, 0.1);
      backdrop-filter: blur(10px);
      z-index: 9998;
      display: flex;
      flex-direction: column;
      opacity: 0;
      transform: translateY(-10px) scale(0.95);
      pointer-events: none;
      transition: all 0.2s ease;
      
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
        color: #00CED1;
      }
      
      .header-title {
        flex: 1;
        color: rgba(255, 255, 255, 0.95);
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
          color: rgba(255, 255, 255, 0.7);
        }
        
        &:hover {
          background: rgba(255, 255, 255, 0.1);
          
          mat-icon {
            color: white;
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
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.85rem;
      
      mat-icon {
        font-size: 32px;
        width: 32px;
        height: 32px;
        color: #ef4444;
      }
    }

    .spinner {
      width: 28px;
      height: 28px;
      border: 3px solid rgba(0, 71, 171, 0.2);
      border-top-color: #00CED1;
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
        background: rgba(255, 255, 255, 0.05);
      }
      
      &::-webkit-scrollbar-thumb {
        background: rgba(0, 71, 171, 0.5);
        border-radius: 3px;
      }
      
      &::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 71, 171, 0.7);
      }
    }

    .yaml-code {
      font-family: 'Roboto Mono', 'Courier New', monospace;
      font-size: 0.8rem;
      line-height: 1.6;
      color: rgba(255, 255, 255, 0.9);
      margin: 0;
      white-space: pre;
      word-wrap: normal;
      overflow-x: auto;
      
      /* YAML syntax highlighting (manual) */
      /* Keys are turquoise */
    }

    .popover-footer {
      padding: 0.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      display: flex;
      justify-content: flex-end;
      
      .refresh-btn {
        background: rgba(0, 71, 171, 0.2);
        border: 1px solid rgba(0, 71, 171, 0.4);
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
          color: #00CED1;
        }
        
        &:hover {
          background: rgba(0, 71, 171, 0.3);
          border-color: rgba(0, 71, 171, 0.6);
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

