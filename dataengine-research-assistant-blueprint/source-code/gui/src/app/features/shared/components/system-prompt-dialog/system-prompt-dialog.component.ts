import { ChangeDetectionStrategy, Component, inject, signal, computed } from '@angular/core';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';
import { SystemPromptService } from '../../services/system-prompt.service';

@Component({
  selector: 'app-system-prompt-dialog',
  standalone: true,
  imports: [
    MatDialogModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    FormsModule,
  ],
  template: `
    <div class="prompt-dialog">
      <div class="prompt-dialog__header">
        <div class="prompt-dialog__title">
          <mat-icon>psychology</mat-icon>
          <span>System Prompt</span>
        </div>
        <button class="prompt-dialog__close-btn" (click)="close()" matTooltip="Close">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <textarea
        class="prompt-dialog__textarea"
        [ngModel]="editingPrompt()"
        (ngModelChange)="editingPrompt.set($event)"
        placeholder="Enter system prompt..."
        rows="12"></textarea>

      <div class="prompt-dialog__footer">
        <div class="prompt-dialog__footer-left">
          <button class="prompt-dialog__reset-btn" (click)="reset()" matTooltip="Restore to default system prompt">
            <mat-icon>restart_alt</mat-icon>
            <span>Restore Default</span>
          </button>
          @if (promptService.hasCustomPrompt()) {
            <span class="prompt-dialog__badge">Custom prompt active</span>
          }
          @if (hasUnsavedChanges()) {
            <span class="prompt-dialog__badge prompt-dialog__badge--unsaved">Unsaved changes</span>
          }
        </div>
        <button class="prompt-dialog__save-btn" (click)="save()" [disabled]="!hasUnsavedChanges()">
          <mat-icon>save</mat-icon>
          <span>Save</span>
        </button>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }

    .prompt-dialog {
      padding: 1.25rem;
      box-sizing: border-box;

      &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
      }

      &__title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #E8EBEC;
        font-size: 1rem;
        font-weight: 600;

        mat-icon {
          font-size: 1.25rem;
          width: 1.25rem;
          height: 1.25rem;
          color: #00CEFF;
        }
      }

      &__close-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        padding: 0;
        border: none;
        border-radius: 0.375rem;
        background: rgba(255, 255, 255, 0.1);
        color: #BCC5D4;
        cursor: pointer;
        transition: all 150ms ease;

        mat-icon {
          font-size: 1.125rem;
          width: 1.125rem;
          height: 1.125rem;
        }

        &:hover {
          background: rgba(255, 255, 255, 0.2);
          color: #E8EBEC;
        }
      }

      &__textarea {
        width: 100%;
        min-height: 240px;
        padding: 0.75rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 0.5rem;
        background: rgba(0, 0, 0, 0.2);
        color: #E8EBEC;
        font-size: 0.8125rem;
        font-family: 'Source Code Pro', monospace;
        line-height: 1.5;
        resize: vertical;
        outline: none;
        box-sizing: border-box;
        transition: border-color 150ms ease;

        &:focus {
          border-color: #00CEFF;
        }

        &::placeholder {
          color: #6B7280;
        }
      }

      &__footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-top: 1rem;
      }

      &__footer-left {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
      }

      &__reset-btn {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.375rem 0.75rem;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 0.375rem;
        background: rgba(255, 255, 255, 0.06);
        color: #BCC5D4;
        cursor: pointer;
        font-size: 0.75rem;
        font-weight: 500;
        transition: all 150ms ease;

        mat-icon {
          font-size: 1rem;
          width: 1rem;
          height: 1rem;
        }

        &:hover {
          background: rgba(255, 255, 255, 0.12);
          color: #E8EBEC;
          border-color: rgba(255, 255, 255, 0.25);
        }
      }

      &__save-btn {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.375rem 1rem;
        border: 1px solid rgba(0, 206, 255, 0.4);
        border-radius: 0.375rem;
        background: rgba(0, 206, 255, 0.15);
        color: #00CEFF;
        cursor: pointer;
        font-size: 0.8rem;
        font-weight: 600;
        transition: all 150ms ease;
        flex-shrink: 0;

        mat-icon {
          font-size: 1rem;
          width: 1rem;
          height: 1rem;
        }

        &:hover:not(:disabled) {
          background: rgba(0, 206, 255, 0.25);
        }

        &:disabled {
          opacity: 0.35;
          cursor: default;
        }
      }

      &__badge {
        padding: 0.25rem 0.5rem;
        background: rgba(0, 206, 255, 0.15);
        border: 1px solid rgba(0, 206, 255, 0.3);
        border-radius: 0.25rem;
        color: #00CEFF;
        font-size: 0.7rem;
        font-weight: 500;

        &--unsaved {
          background: rgba(255, 183, 0, 0.15);
          border-color: rgba(255, 183, 0, 0.3);
          color: #FFB700;
        }
      }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SystemPromptDialogComponent {
  promptService = inject(SystemPromptService);
  private dialogRef = inject(MatDialogRef<SystemPromptDialogComponent>);

  editingPrompt = signal(this.promptService.customSystemPrompt());

  hasUnsavedChanges = computed(() =>
    this.editingPrompt() !== this.promptService.customSystemPrompt()
  );

  save(): void {
    this.promptService.savePrompt(this.editingPrompt());
  }

  reset(): void {
    this.promptService.resetPrompt();
    this.editingPrompt.set(this.promptService.defaultSystemPrompt());
  }

  close(): void {
    this.dialogRef.close();
  }
}
