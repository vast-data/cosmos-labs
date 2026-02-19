import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { SETTINGS } from '../../shared/settings';
import { SessionsResponse } from '../../shared/models/sessions.model';
import { MOCK_SESSIONS_RESPONSE } from './sessions.mocks';

@Injectable({
  providedIn: 'root'
})
export class SessionsApiService {
  private httpClient = inject(HttpClient);

  getSessions(limit = 1000): Observable<SessionsResponse> {
    if (SETTINGS.MOCK_MODE) {
      return of(MOCK_SESSIONS_RESPONSE);
    }

    let params = new HttpParams();
    if (limit) {
      params = params.set('limit', limit.toString());
    }

    return this.httpClient.get<SessionsResponse>(`${SETTINGS.BASE_API_URL}/sessions`, { params });
  }
}
