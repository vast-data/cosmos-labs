import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

import { SETTINGS } from '../../shared/settings';
import { AuthService } from '../../auth/services/auth.service';
import { SessionResponse } from './session.mapper';

@Injectable({
  providedIn: 'root'
})
export class ReportApiService {
  private readonly http = inject(HttpClient);
  private readonly authService = inject(AuthService);

  getSession(sessionId: string): Observable<SessionResponse> {
    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.authService.token()}`
    });

    return this.http.get<SessionResponse>(
      `${SETTINGS.BASE_API_URL}/sessions/${sessionId}`,
      { headers }
    );
  }
}

