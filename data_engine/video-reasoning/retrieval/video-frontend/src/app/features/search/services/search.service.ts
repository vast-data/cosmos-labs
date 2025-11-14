import { Injectable, inject, signal } from '@angular/core';
import { VideoService } from '../../../shared/services/video.service';
import { SearchRequest, SearchResponse, VideoSearchResult, LLMSynthesis } from '../../../shared/models/video.model';

export interface SearchState {
  loading: boolean;
  results: VideoSearchResult[];
  query: string;
  error: string | null;
  embeddingTimeMs: number;
  searchTimeMs: number;
  llmTimeMs: number;
  permissionFiltered: number;
  llmSynthesis: LLMSynthesis | null;
  animationPhase: 'idle' | 'embedding' | 'searching' | 'filtering' | 'synthesizing' | 'complete';
}

@Injectable({
  providedIn: 'root'
})
export class SearchService {
  private videoService = inject(VideoService);

  state = signal<SearchState>({
    loading: false,
    results: [],
    query: '',
    error: null,
    embeddingTimeMs: 0,
    searchTimeMs: 0,
    llmTimeMs: 0,
    permissionFiltered: 0,
    llmSynthesis: null,
    animationPhase: 'idle'
  });

  async search(request: SearchRequest) {
    this.state.update(s => ({
      ...s,
      loading: true,
      error: null,
      query: request.query,
      animationPhase: 'embedding'
    }));

    try {
      // Simulate embedding phase for animation
      await this.delay(800);
      
      this.state.update(s => ({ ...s, animationPhase: 'searching' }));
      await this.delay(400);

      // Actual API call
      const response = await this.videoService.search(request).toPromise();

      if (response) {
        this.state.update(s => ({ ...s, animationPhase: 'filtering' }));
        await this.delay(600);

        // Show LLM synthesis phase if enabled
        if (request.use_llm && response.results.length > 0) {
          this.state.update(s => ({ ...s, animationPhase: 'synthesizing' }));
          await this.delay(800);
        }

        // Small delay before showing complete to smooth transition
        await this.delay(200);

        this.state.update(s => ({
          ...s,
          loading: false,
          results: response.results,
          embeddingTimeMs: response.embedding_time_ms,
          searchTimeMs: response.search_time_ms,
          llmTimeMs: response.llm_synthesis?.processing_time ? response.llm_synthesis.processing_time * 1000 : 0,
          permissionFiltered: response.permission_filtered,
          llmSynthesis: response.llm_synthesis || null,
          animationPhase: 'complete'
        }));
      }
    } catch (error: any) {
      this.state.update(s => ({
        ...s,
        loading: false,
        error: error.error?.detail || 'Search failed. Please try again.',
        animationPhase: 'idle'
      }));
    }
  }

  clearResults() {
    this.state.update(s => ({
      ...s,
      results: [],
      query: '',
      error: null,
      embeddingTimeMs: 0,
      searchTimeMs: 0,
      llmTimeMs: 0,
      llmSynthesis: null,
      animationPhase: 'idle'
    }));
  }

  closeAnimation() {
    this.state.update(s => ({
      ...s,
      animationPhase: 'idle'
    }));
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

