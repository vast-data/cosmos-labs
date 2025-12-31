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
      background: linear-gradient(135deg, #0A0A1E 0%, #15152E 100%);
      color: white;
      min-width: 600px;
      max-width: 900px;
      max-height: 85vh;
    }

    .dialog-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.25rem 1.5rem;
      background: rgba(0, 0, 0, 0.2);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);

      .header-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;

        mat-icon {
          color: #00CED1;
          font-size: 1.5rem;
          width: 1.5rem;
          height: 1.5rem;
        }

        h2 {
          margin: 0;
          font-size: 1.2rem;
          font-weight: 600;
        }
      }

      .close-btn {
        color: rgba(255, 255, 255, 0.7);
        &:hover {
          color: white;
          background: rgba(255, 255, 255, 0.1);
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
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.9rem;
        line-height: 1.5;

        strong {
          color: #00CED1;
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
          color: #00CED1;
          font-size: 0.9rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
      }

      .sql-display {
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(0, 206, 209, 0.3);
        border-radius: 8px;
        padding: 1rem;
        overflow-x: auto;
        max-height: 400px;
        overflow-y: auto;

        pre {
          margin: 0;
          padding: 0;
          font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
          font-size: 0.85rem;
          line-height: 1.6;
          color: rgba(255, 255, 255, 0.9);
          white-space: pre-wrap;
          word-wrap: break-word;

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
      background: rgba(0, 206, 209, 0.1);
      border: 1px solid rgba(0, 206, 209, 0.3);
      border-radius: 8px;

      mat-icon {
        color: #00CED1;
        flex-shrink: 0;
      }

      .info-content {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.85);

        strong {
          display: block;
          margin-bottom: 0.5rem;
        }

        ul {
          margin: 0;
          padding-left: 1.25rem;
          
          li {
            margin-bottom: 0.25rem;
            line-height: 1.4;

            code {
              background: rgba(0, 0, 0, 0.3);
              padding: 0.125rem 0.375rem;
              border-radius: 4px;
              font-family: 'JetBrains Mono', 'Fira Code', monospace;
              font-size: 0.9em;
              color: #00CED1;
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

