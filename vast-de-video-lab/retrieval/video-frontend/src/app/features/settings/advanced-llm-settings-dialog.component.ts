import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatSliderModule } from '@angular/material/slider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

// Storage keys for localStorage
export const LLM_SETTINGS_STORAGE_KEY = 'video_lab_llm_settings';

export interface LLMSettings {
  llmTopNSummaries: number;    // How many results sent to LLM (3, 5, 10)
  searchTopK: number;          // Max search results from VastDB (5, 10, 15)
  minSimilarityScore: number;  // Minimum similarity threshold (0.1 - 0.8)
}

export const DEFAULT_LLM_SETTINGS: LLMSettings = {
  llmTopNSummaries: 3,
  searchTopK: 15,
  minSimilarityScore: 0.1
};

// Helper function to get settings (can be used by other components)
export function getLLMSettings(): LLMSettings {
  const stored = localStorage.getItem(LLM_SETTINGS_STORAGE_KEY);
  if (stored) {
    try {
      return { ...DEFAULT_LLM_SETTINGS, ...JSON.parse(stored) };
    } catch {
      return DEFAULT_LLM_SETTINGS;
    }
  }
  return DEFAULT_LLM_SETTINGS;
}

@Component({
  selector: 'app-advanced-llm-settings-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatSliderModule,
    MatTooltipModule,
    MatSnackBarModule
  ],
  template: `
    <div class="dialog-container">
      <div class="dialog-header">
        <div class="header-title">
          <mat-icon>tune</mat-icon>
          <h2>Advanced LLM Settings</h2>
        </div>
        <button mat-icon-button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-content">
        <p class="description">
          Fine-tune the search and AI analysis parameters to optimize results for your use case.
          These settings are stored in your browser and persist across sessions.
        </p>

        <!-- LLM Analysis Count -->
        <div class="setting-row">
          <div class="setting-label">
            <span class="label-text">LLM Analysis Count</span>
            <button mat-icon-button class="info-btn"
                    matTooltip="Number of top search results sent to the LLM for analysis and response synthesis. Only applies when 'Enable LLM Response' toggle is enabled. Higher values provide more context but may increase response time."
                    matTooltipPosition="right">
              <mat-icon>info_outline</mat-icon>
            </button>
          </div>
          <mat-form-field appearance="outline" class="setting-field">
            <mat-select [(ngModel)]="settings.llmTopNSummaries">
              <mat-option [value]="3">3 results</mat-option>
              <mat-option [value]="5">5 results</mat-option>
              <mat-option [value]="10">10 results</mat-option>
            </mat-select>
          </mat-form-field>
        </div>

        <!-- Max Search Results -->
        <div class="setting-row">
          <div class="setting-label">
            <span class="label-text">Max Search Results</span>
            <button mat-icon-button class="info-btn"
                    matTooltip="Maximum number of video segments to retrieve from the database. Higher values may include more relevant results but increase response time and display more cards."
                    matTooltipPosition="right">
              <mat-icon>info_outline</mat-icon>
            </button>
          </div>
          <mat-form-field appearance="outline" class="setting-field">
            <mat-select [(ngModel)]="settings.searchTopK">
              <mat-option [value]="5">5 results</mat-option>
              <mat-option [value]="10">10 results</mat-option>
              <mat-option [value]="15">15 results</mat-option>
            </mat-select>
          </mat-form-field>
        </div>

        <!-- Minimum Similarity Score -->
        <div class="setting-row slider-row">
          <div class="setting-label">
            <span class="label-text">Minimum Similarity</span>
            <button mat-icon-button class="info-btn"
                    matTooltip="Threshold for matching relevance. Lower values (0.1) return more results but may include less relevant matches. Higher values (0.8) are stricter and return only highly relevant matches. Recommended: 0.4-0.6"
                    matTooltipPosition="right">
              <mat-icon>info_outline</mat-icon>
            </button>
          </div>
          <div class="slider-container">
            <div class="slider-labels">
              <span class="slider-label">Broad (0.1)</span>
              <span class="slider-value">{{ settings.minSimilarityScore.toFixed(2) }}</span>
              <span class="slider-label">Strict (0.8)</span>
            </div>
            <mat-slider min="0.1" max="0.8" step="0.05" class="similarity-slider">
              <input matSliderThumb [(ngModel)]="settings.minSimilarityScore">
            </mat-slider>
          </div>
        </div>

        <!-- Info Box -->
        <div class="info-box">
          <mat-icon>lightbulb</mat-icon>
          <div class="info-content">
            <strong>Tips:</strong>
            <ul>
              <li>For broad exploration, use lower similarity (0.3-0.4) and more results</li>
              <li>For precise queries, use higher similarity (0.6-0.8) and fewer results</li>
              <li>LLM Analysis Count should not exceed Max Search Results</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="dialog-actions">
        <button mat-button class="reset-btn" (click)="resetToDefaults()">
          <mat-icon>refresh</mat-icon>
          Reset Defaults
        </button>
        <div class="action-buttons">
          <button mat-button class="cancel-btn" (click)="close()">Cancel</button>
          <button mat-raised-button class="save-btn" (click)="save()">
            <mat-icon>save</mat-icon>
            Save Settings
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dialog-container {
      background: linear-gradient(135deg, #0A0A1E 0%, #15152E 100%);
      color: white;
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      min-width: 500px;
    }

    .dialog-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.5rem;
      background: rgba(0, 0, 0, 0.2);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);

      .header-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;

        h2 {
          margin: 0;
          font-size: 1.2rem;
          font-weight: 600;
          color: #00CED1;
        }

        mat-icon {
          font-size: 1.8rem;
          width: 1.8rem;
          height: 1.8rem;
          color: #00CED1;
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
      gap: 1.5rem;
    }

    .description {
      font-size: 0.9rem;
      color: rgba(255, 255, 255, 0.7);
      line-height: 1.5;
      margin: 0;
    }

    .setting-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      
      &.slider-row {
        flex-direction: column;
        align-items: stretch;
      }
    }

    .setting-label {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      flex-shrink: 0;

      .label-text {
        font-size: 0.95rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.9);
      }

      .info-btn {
        width: 24px;
        height: 24px;
        line-height: 24px;
        
        mat-icon {
          font-size: 16px;
          width: 16px;
          height: 16px;
          color: rgba(0, 206, 209, 0.7);
        }
        
        &:hover mat-icon {
          color: #00CED1;
        }
      }
    }

    .setting-field {
      width: 160px;
      
      ::ng-deep {
        .mat-mdc-form-field-flex {
          background: rgba(0, 0, 0, 0.3) !important;
        }

        .mat-mdc-text-field-wrapper {
          background: transparent !important;
        }

        .mdc-notched-outline__leading,
        .mdc-notched-outline__notch,
        .mdc-notched-outline__trailing {
          border-color: rgba(255, 255, 255, 0.2) !important;
        }

        .mat-mdc-select-value {
          color: white !important;
        }

        .mat-mdc-select-arrow {
          color: rgba(255, 255, 255, 0.7) !important;
        }
      }
    }

    .slider-container {
      width: 100%;
      padding: 0 0.5rem;
    }

    .slider-labels {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.25rem;
      
      .slider-label {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.5);
      }
      
      .slider-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        font-weight: 600;
        color: #00CED1;
        background: rgba(0, 206, 209, 0.1);
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
      }
    }

    .similarity-slider {
      width: 100%;
      
      ::ng-deep {
        .mdc-slider__track--inactive {
          background: rgba(255, 255, 255, 0.2) !important;
        }
        
        .mdc-slider__track--active_fill {
          background: linear-gradient(90deg, #00CED1, #0047AB) !important;
          border-color: transparent !important;
        }
        
        .mdc-slider__thumb-knob {
          background: #00CED1 !important;
          border-color: #00CED1 !important;
          box-shadow: 0 0 10px rgba(0, 206, 209, 0.5);
        }
      }
    }

    .info-box {
      display: flex;
      align-items: flex-start;
      gap: 1rem;
      background: rgba(0, 71, 171, 0.15);
      border: 1px solid rgba(0, 71, 171, 0.3);
      border-radius: 8px;
      padding: 1rem;
      font-size: 0.85rem;
      color: rgba(255, 255, 255, 0.8);

      mat-icon {
        color: #F59E0B;
        font-size: 1.5rem;
        width: 1.5rem;
        height: 1.5rem;
        flex-shrink: 0;
      }

      ul {
        margin: 0.5rem 0 0 0;
        padding-left: 1.2rem;
      }

      li {
        margin-bottom: 0.3rem;
        &:last-child {
          margin-bottom: 0;
        }
      }
    }

    .dialog-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(0, 0, 0, 0.2);

      .reset-btn {
        color: rgba(255, 255, 255, 0.6);
        mat-icon {
          margin-right: 0.25rem;
        }
        &:hover {
          color: white;
          background: rgba(255, 255, 255, 0.1);
        }
      }

      .action-buttons {
        display: flex;
        gap: 1rem;
      }

      .cancel-btn {
        color: rgba(255, 255, 255, 0.7);
        &:hover {
          background: rgba(255, 255, 255, 0.1);
        }
      }

      .save-btn {
        background: linear-gradient(135deg, #0047AB 0%, #002766 100%) !important;
        color: white !important;
        mat-icon {
          margin-right: 0.5rem;
        }
        &:hover {
          box-shadow: 0 4px 12px rgba(0, 71, 171, 0.6);
        }
      }
    }
  `]
})
export class AdvancedLLMSettingsDialogComponent implements OnInit {
  private dialogRef = inject(MatDialogRef<AdvancedLLMSettingsDialogComponent>);
  private snackBar = inject(MatSnackBar);

  settings: LLMSettings = { ...DEFAULT_LLM_SETTINGS };

  ngOnInit() {
    this.loadSettings();
  }

  loadSettings() {
    this.settings = getLLMSettings();
  }

  resetToDefaults() {
    this.settings = { ...DEFAULT_LLM_SETTINGS };
    this.snackBar.open('Settings reset to defaults', 'OK', {
      duration: 2000,
      panelClass: 'info-snackbar'
    });
  }

  save() {
    // Validate: llmTopNSummaries should not exceed searchTopK
    if (this.settings.llmTopNSummaries > this.settings.searchTopK) {
      this.snackBar.open('LLM Analysis Count cannot exceed Max Search Results. Adjusting...', 'OK', {
        duration: 3000,
        panelClass: 'warning-snackbar'
      });
      this.settings.llmTopNSummaries = Math.min(this.settings.llmTopNSummaries, this.settings.searchTopK);
    }

    localStorage.setItem(LLM_SETTINGS_STORAGE_KEY, JSON.stringify(this.settings));
    this.snackBar.open('Settings saved!', 'OK', {
      duration: 2000,
      panelClass: 'success-snackbar'
    });
    this.dialogRef.close(true);
  }

  close() {
    this.dialogRef.close(false);
  }
}

