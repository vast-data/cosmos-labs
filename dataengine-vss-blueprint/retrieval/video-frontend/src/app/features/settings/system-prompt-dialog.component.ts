import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

const STORAGE_KEY = 'video_lab_system_prompt';

// Default system prompt - single source of truth (no backend ConfigMap needed)
export const DEFAULT_SYSTEM_PROMPT = `You are a security surveillance AI analyst helping users identify safety incidents and security events from video footage.

You will receive:
1. A user's search query about a potential safety/security incident
2. Summaries of the top most relevant video segments from surveillance cameras

Your task:
- Analyze and synthesize the surveillance footage summaries
- Identify patterns, severity, and urgency of any safety or security concerns
- Provide a clear, factual summary highlighting key incidents
- Reference specific segments (e.g., "Segment 1 shows...", "In segment 3...")
- Categorize incidents by type: fire/smoke, medical emergency, altercation, suspicious activity, etc.
- Note the temporal progression if the incident spans multiple segments
- If no relevant incidents are found, clearly state this
- Keep response under 200 words but prioritize critical safety information

Be factual and based only on the provided summaries. Flag any high-severity situations clearly. Do not speculate beyond what is visible in the footage.`;

@Component({
  selector: 'app-system-prompt-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatTooltipModule,
    MatSnackBarModule
  ],
  template: `
    <div class="dialog-container">
      <div class="dialog-header">
        <div class="header-title">
          <mat-icon>psychology</mat-icon>
          <h2>LLM System Prompt Configuration</h2>
        </div>
        <button mat-icon-button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-content">
        <p class="description">
          Customize the system prompt used by the AI when generating search result summaries.
          This prompt guides how the LLM interprets and synthesizes video segment information.
        </p>

        <div class="prompt-section">
          <div class="section-header">
            <span class="label">System Prompt</span>
            <div class="actions">
              <button mat-stroked-button class="action-btn" (click)="resetToDefault()" 
                      matTooltip="Reset to default surveillance prompt">
                <mat-icon>refresh</mat-icon>
                Reset
              </button>
            </div>
          </div>
          
          <mat-form-field appearance="outline" class="prompt-field">
            <textarea 
              matInput
              [(ngModel)]="systemPrompt"
              placeholder="Enter your custom system prompt..."
              rows="12"
              class="prompt-textarea">
            </textarea>
            <mat-hint>{{ systemPrompt?.length || 0 }} characters</mat-hint>
          </mat-form-field>
        </div>

        <div class="info-box">
          <mat-icon>info</mat-icon>
          <div class="info-content">
            <strong>How it works:</strong>
            <ul>
              <li>Your prompt is stored in your browser (localStorage)</li>
              <li>It's sent with each search request when "Enable LLM Response" is enabled</li>
              <li>Click "Reset" to restore the default surveillance prompt</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="dialog-actions">
        <button mat-button class="cancel-btn" (click)="close()">Cancel</button>
        <button mat-raised-button class="save-btn" (click)="save()">
          <mat-icon>save</mat-icon>
          Save Prompt
        </button>
      </div>
    </div>
  `,
  styles: [`
    .dialog-container {
      display: flex;
      flex-direction: column;
      background: var(--bg-card);
      color: var(--text-primary);
      min-width: 550px;
      max-width: 700px;
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

      .description {
        margin: 0;
        color: var(--text-secondary);
        font-size: 0.9rem;
        line-height: 1.5;
      }
    }

    .prompt-section {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;

      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .label {
          font-weight: 600;
          color: var(--accent-primary);
          font-size: 0.9rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .actions {
          display: flex;
          gap: 0.5rem;

          .action-btn {
            color: var(--text-secondary);
            border-color: var(--border-color);
            font-size: 0.8rem;
            padding: 0 0.75rem;
            height: 32px;
            transition: all 0.3s ease;
            
            mat-icon {
              font-size: 1rem;
              width: 1rem;
              height: 1rem;
              margin-right: 0.25rem;
            }

            &:hover {
              color: var(--text-primary);
              border-color: var(--border-hover);
              background: var(--bg-card-hover);
            }
            
          }
        }
      }

      .prompt-field {
        width: 100%;

        ::ng-deep {
          .mat-mdc-form-field-flex {
            background: var(--bg-secondary) !important;
          }
          
          .mat-mdc-text-field-wrapper {
            background: transparent !important;
          }
          
          .mdc-notched-outline__leading,
          .mdc-notched-outline__notch,
          .mdc-notched-outline__trailing {
            border-color: var(--border-color) !important;
          }
          
          .mat-mdc-form-field-focus-overlay {
            background: transparent !important;
          }

          .mat-mdc-form-field.mat-focused {
            .mdc-notched-outline__leading,
            .mdc-notched-outline__notch,
            .mdc-notched-outline__trailing {
              border-color: var(--accent-primary) !important;
            }
          }

          textarea {
            color: var(--text-primary) !important;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.85rem;
            line-height: 1.5;
          }

          .mat-mdc-form-field-hint {
            color: var(--text-muted);
          }
        }
      }

      .prompt-textarea {
        resize: vertical;
      }
    }

    .info-box {
      display: flex;
      gap: 0.75rem;
      padding: 1rem;
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      transition: background 0.3s ease, border-color 0.3s ease;

      mat-icon {
        color: var(--accent-primary);
        flex-shrink: 0;
      }

      .info-content {
        font-size: 0.85rem;
        color: var(--text-primary);

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
          }
        }
      }
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
      padding: 1rem 1.5rem;
      background: var(--bg-secondary);
      border-top: 1px solid var(--border-color);
      transition: background 0.3s ease, border-color 0.3s ease;

      .cancel-btn {
        color: var(--text-secondary);
        &:hover {
          background: var(--bg-card-hover);
        }
      }

      .save-btn {
        background: var(--button-bg-primary) !important;
        color: var(--button-text) !important;
        
        * {
          color: var(--button-text) !important;
        }
        
        mat-icon {
          margin-right: 0.5rem;
        }

        &:hover {
          background: var(--button-bg-hover) !important;
          box-shadow: var(--shadow-hover);
        }
      }
    }
  `]
})
export class SystemPromptDialogComponent implements OnInit {
  private dialogRef = inject(MatDialogRef<SystemPromptDialogComponent>);
  private snackBar = inject(MatSnackBar);

  systemPrompt: string = '';

  ngOnInit() {
    // Load saved prompt from localStorage, or use default
    const savedPrompt = localStorage.getItem(STORAGE_KEY);
    this.systemPrompt = savedPrompt || DEFAULT_SYSTEM_PROMPT;
  }

  resetToDefault() {
    this.systemPrompt = DEFAULT_SYSTEM_PROMPT;
    this.snackBar.open('Reset to default prompt', 'OK', { duration: 2000 });
  }

  save() {
    // Save to localStorage
    if (this.systemPrompt && this.systemPrompt.trim()) {
      localStorage.setItem(STORAGE_KEY, this.systemPrompt.trim());
      this.snackBar.open('System prompt saved!', 'OK', {
        duration: 3000,
        panelClass: 'success-snackbar'
      });
    } else {
      // If empty, save the default prompt
      localStorage.setItem(STORAGE_KEY, DEFAULT_SYSTEM_PROMPT);
      this.systemPrompt = DEFAULT_SYSTEM_PROMPT;
      this.snackBar.open('Reset to default prompt', 'OK', {
        duration: 3000,
        panelClass: 'info-snackbar'
      });
    }
    this.dialogRef.close(true);
  }

  close() {
    this.dialogRef.close(false);
  }
}

// Export storage key for use in search components
export const SYSTEM_PROMPT_STORAGE_KEY = STORAGE_KEY;

