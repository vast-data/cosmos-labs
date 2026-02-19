import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface BatchSyncCheckObjectsRequest {
  access_key: string;
  secret_key: string;
  s3_endpoint: string;
  bucket: string;
  prefix: string;
  use_ssl?: boolean;
}

export interface BatchSyncStartRequest {
  // Source S3 configuration
  source_access_key: string;
  source_secret_key: string;
  source_s3_endpoint: string;
  source_bucket: string;
  source_prefix: string;
  source_use_ssl?: boolean;
  
  // Destination S3 configuration (optional, uses backend default)
  dest_access_key?: string;
  dest_secret_key?: string;
  dest_s3_endpoint?: string;
  dest_bucket?: string;
  dest_use_ssl?: boolean;
  
  // Batch sync configuration
  batch_size: number;
  
  // Video metadata
  is_public: boolean;
  tags?: string[];
  allowed_users?: string[];
  
  // Streaming metadata (optional)
  camera_id?: string;
  capture_type?: string;
  neighborhood?: string;
  scenario?: string;  // Analysis scenario (surveillance, traffic, egocentric, etc.)
}

export interface BatchSyncStatus {
  success: boolean;
  status: {
    job_id: string;
    status: string;  // running, completed, failed
    total_files: number;
    completed_files: number;
    failed_files: number;
    failed_file_list: any[];
    start_time: string;
    end_time: string | null;
    current_file: string | null;
    source_bucket?: string;
    source_prefix?: string;
    dest_bucket?: string;
  } | null;
  message?: string;
}

export interface BatchSyncOperationResponse {
  success: boolean;
  message?: string;
  error?: string;
  job_id?: string;
}

export interface BatchSyncCheckObjectsResponse {
  success: boolean;
  count: number;
  files?: any[];
  error?: string;
}

export interface BatchSyncPrefillConfig {
  s3_endpoint: string;
  s3_access_key: string;
  s3_secret_key: string;
  bucket_name: string;
}

@Injectable({
  providedIn: 'root'
})
export class BatchSyncService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/batch-sync`;

  /**
   * Get S3 configuration for pre-filling the batch sync form
   */
  getPrefillConfig(): Observable<BatchSyncPrefillConfig> {
    return this.http.get<BatchSyncPrefillConfig>(`${this.apiUrl}/prefill`);
  }

  /**
   * Check and count MP4 files in source S3 bucket
   */
  checkObjects(request: BatchSyncCheckObjectsRequest): Observable<BatchSyncCheckObjectsResponse> {
    return this.http.post<BatchSyncCheckObjectsResponse>(`${this.apiUrl}/check-objects`, request);
  }

  /**
   * Start batch sync operation
   */
  start(request: BatchSyncStartRequest): Observable<BatchSyncOperationResponse> {
    return this.http.post<BatchSyncOperationResponse>(`${this.apiUrl}/start`, request);
  }

  /**
   * Get batch sync status for current user
   */
  getStatus(): Observable<BatchSyncStatus> {
    return this.http.get<BatchSyncStatus>(`${this.apiUrl}/status`);
  }

  /**
   * Stop active batch sync operation
   */
  stop(): Observable<BatchSyncOperationResponse> {
    return this.http.post<BatchSyncOperationResponse>(`${this.apiUrl}/stop`, {});
  }
}

