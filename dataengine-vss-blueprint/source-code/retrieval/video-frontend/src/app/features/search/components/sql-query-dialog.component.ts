import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

export interface SqlQueryDialogData {
  sqlQuery: string;
  userQuery: string;
}

@Component({
  selector: 'app-sql-query-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule
  ],
  template: `
    <div class="dialog-container">
      <div class="dialog-header">
        <div class="header-title">
          <mat-icon>code</mat-icon>
          <h2>Similarity Search Query</h2>
        </div>
        <button mat-icon-button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-content">
        <p class="description">
          This is the ADBC SQL query executed against VastDB for your search:
          <strong>"{{ data.userQuery }}"</strong>
        </p>

        <div class="query-section">
          <div class="section-header">
            <span class="label">SQL Query</span>
          </div>
          
          <div class="sql-display">
            <pre><code>{{ data.sqlQuery }}</code></pre>
          </div>
        </div>

        <div class="info-box">
          <mat-icon>info</mat-icon>
          <div class="info-content">
            <strong>Note:</strong>
            <ul>
              <li>The embedding vector has been replaced with your query text for readability</li>
              <li>This query uses <code>array_cosine_distance</code> for semantic similarity search</li>
              <li>Results are ordered by similarity distance (lower = more similar)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dialog-container {
      display: flex;
      flex-direction: column;
      background: var(--bg-card);
      color: var(--text-primary);
      min-width: 600px;
      max-width: 900px;
      max-height: 85vh;
      transition: background 0.3s ease, color 0.3s ease;
    }

    .dialog-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.25rem 1.5rem;
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border-color);
      transition: background 0.3s ease, border-color 0.3s ease;

      .header-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;

        mat-icon {
          color: var(--accent-primary);
          font-size: 1.5rem;
          width: 1.5rem;
          height: 1.5rem;
        }

        h2 {
          margin: 0;
          font-size: 1.2rem;
          font-weight: 600;
          color: var(--text-primary);
        }
      }

      .close-btn {
        color: var(--text-secondary);
        &:hover {
          color: var(--text-primary);
          background: var(--bg-card-hover);
        }
      }
    }

    .dialog-content {
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      overflow-y: auto;
      flex: 1;

      .description {
        margin: 0;
        color: var(--text-secondary);
        font-size: 0.9rem;
        line-height: 1.5;

        strong {
          color: var(--accent-primary);
        }
      }
    }

    .query-section {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;

      .section-header {
        display: flex;
        justify-content: flex-start;
        align-items: center;

        .label {
          font-weight: 600;
          color: var(--accent-primary);
          font-size: 0.9rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
      }

      .sql-display {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        overflow-x: auto;
        max-height: 400px;
        overflow-y: auto;
        transition: background 0.3s ease, border-color 0.3s ease;

        pre {
          margin: 0;
          padding: 0;
          font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
          font-size: 0.85rem;
          line-height: 1.6;
          color: var(--text-primary);
          white-space: pre-wrap;
          word-wrap: break-word;
          transition: color 0.3s ease;

          code {
            font-family: inherit;
            color: inherit;
          }
        }
      }
    }

    .info-box {
      display: flex;
      gap: 0.75rem;
      padding: 1rem;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      transition: background 0.3s ease, border-color 0.3s ease;

      mat-icon {
        color: var(--accent-primary);
        flex-shrink: 0;
      }

      .info-content {
        font-size: 0.85rem;
        color: var(--text-secondary);

        strong {
          display: block;
          margin-bottom: 0.5rem;
          color: var(--text-primary);
        }

        ul {
          margin: 0;
          padding-left: 1.25rem;
          
          li {
            margin-bottom: 0.25rem;
            line-height: 1.4;

            code {
              background: var(--bg-secondary);
              padding: 0.125rem 0.375rem;
              border-radius: 4px;
              font-family: 'JetBrains Mono', 'Fira Code', monospace;
              font-size: 0.9em;
              color: var(--accent-primary);
              border: 1px solid var(--border-color);
            }
          }
        }
      }
    }

  `]
})
export class SqlQueryDialogComponent {
  private dialogRef = inject(MatDialogRef<SqlQueryDialogComponent>);
  data = inject<SqlQueryDialogData>(MAT_DIALOG_DATA);

  close() {
    this.dialogRef.close();
  }
}

