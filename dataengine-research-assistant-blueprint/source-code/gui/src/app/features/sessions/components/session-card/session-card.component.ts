import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Session } from '../../../shared/models/sessions.model';
import { AppStoreService } from '../../../shared/services/app-store.service';
import { ReportApiService } from '../../../reports/services/report-api.service';
import { PdfExportService } from '../../../shared/services/pdf-export.service';
import { mapApiMessagesToChatHistory } from '../../../reports/services/session.mapper';

@Component({
  selector: 'app-session-card',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, MatButtonModule, MatMenuModule, MatSnackBarModule],
  templateUrl: './session-card.component.html',
  styleUrls: ['./session-card.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SessionCardComponent {
  private appStoreService = inject(AppStoreService);
  private reportApi = inject(ReportApiService);
  private pdfService = inject(PdfExportService);
  private snackBar = inject(MatSnackBar);

  session = input.required<Session>();
  className = input<string>('');

  get sessionTitle(): string {
    return this.session().summary?.title || 'Untitled Session';
  }

  onSessionClick(): void {
    this.appStoreService.closeSidebar();
  }

  exportToPdf(): void {
    const s = this.session();
    this.snackBar.open('Preparing PDF...', '', { duration: 3000, horizontalPosition: 'center', verticalPosition: 'bottom' });

    this.reportApi.getSession(s.session_id).subscribe({
      next: (resp) => {
        const chatMessages = mapApiMessagesToChatHistory(resp.messages);
        const title = resp.summary?.title || 'Conversation';
        this.pdfService.exportConversationToPdf(chatMessages, title);
      },
      error: () => {
        this.snackBar.open('Failed to export PDF', '', { duration: 3000, horizontalPosition: 'center', verticalPosition: 'bottom' });
      }
    });
  }
}
