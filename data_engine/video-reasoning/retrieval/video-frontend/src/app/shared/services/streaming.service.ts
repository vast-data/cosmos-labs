import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface StreamingStartRequest {
  youtube_url: string;
  access_key: string;
  secret_key: string;
  s3_endpoint: string;
  name: string;
  bucket_name: string;
  capture_interval: number;
}

export interface StreamingStatus {
  success: boolean;
  status: {
    is_running: boolean;
    current_config: any;
    temp_files_count: number;
  };
  timestamp: string;
}

export interface StreamingOperationResponse {
  success: boolean;
  message?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class StreamingService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/streaming`;

  /**
   * Get streaming service status
   */
  getStatus(): Observable<StreamingStatus> {
    return this.http.get<StreamingStatus>(`${this.apiUrl}/status`);
  }

  /**
   * Start video streaming capture
   */
  start(request: StreamingStartRequest): Observable<StreamingOperationResponse> {
    return this.http.post<StreamingOperationResponse>(`${this.apiUrl}/start`, request);
  }

  /**
   * Stop video streaming capture
   */
  stop(): Observable<StreamingOperationResponse> {
    return this.http.post<StreamingOperationResponse>(`${this.apiUrl}/stop`, {});
  }
}

