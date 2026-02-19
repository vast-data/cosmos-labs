import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { 
  SearchRequest, 
  SearchResponse, 
  UploadRequest, 
  UploadResponse,
  VideoSearchResult 
} from '../models/video.model';

@Injectable({
  providedIn: 'root'
})
export class VideoService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  /**
   * Perform semantic video search
   */
  search(request: SearchRequest): Observable<SearchResponse> {
    return this.http.post<SearchResponse>(`${this.apiUrl}/search`, request);
  }

  /**
   * Get streaming URL for a video
   * 
   * NOTE: The backend proxies the video stream from S3.
   * Token must be in URL because HTML5 <video> elements cannot send custom headers.
   */
  getStreamUrl(source: string, token: string): string {
    // Return the backend stream URL with source and token parameters
    // Token in URL is required because HTML5 video element can't use HTTP interceptor
    const params = new URLSearchParams({ source, token });
    return `${this.apiUrl}/videos/stream?${params.toString()}`;
  }

  /**
   * Get metadata for a specific video segment
   */
  getVideoMetadata(source: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/videos/metadata`, {
      params: { source }
    });
  }

  /**
   * Upload video file directly to backend (backend proxies to S3)
   */
  uploadVideo(file: File, is_public: boolean, tags: string[], allowed_users: string[], scenario: string = ''): Observable<any> {
    console.log('uploadVideo called:', { 
      fileName: file.name, 
      size: file.size, 
      is_public, 
      tags, 
      allowed_users,
      scenario
    });
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('is_public', is_public.toString());
    
    if (tags && tags.length > 0) {
      formData.append('tags', tags.join(','));
    }
    
    if (allowed_users && allowed_users.length > 0) {
      formData.append('allowed_users', allowed_users.join(','));
    }
    
    if (scenario) {
      formData.append('scenario', scenario);
    }
    
    console.log('Uploading to backend...');
    return this.http.post(`${this.apiUrl}/videos/upload`, formData);
  }
}

