import { Injectable, inject, signal, computed, effect } from '@angular/core';
import { SessionsApiService } from './sessions-api.service';
import { SessionsResponse, Session } from '../../shared/models/sessions.model';
import { AuthService } from '../../auth/services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class SessionsService {
  private apiService = inject(SessionsApiService);
  private authService = inject(AuthService);

  private sessionsResponseSignal = signal<SessionsResponse | null>(null);
  private isLoadingSignal = signal(false);
  private hasLoadedOnceSignal = signal(false);
  private errorSignal = signal<string | null>(null);
  private previousTokenSignal = signal<string | null>(null);

  sessions = computed(() => {
    const sessions = this.sessionsResponseSignal()?.sessions || [];
    return sessions.sort((a, b) => b.updated_at - a.updated_at);
  });
  isLoading = computed(() => this.isLoadingSignal() && !this.hasLoadedOnceSignal());
  error = computed(() => this.errorSignal());


  loadSessions() {
    const token = this.authService.token();
    console.log('SessionsService.loadSessions() called, token =', token ? 'present' : 'missing');
    
    // Don't load if no token is available
    if (!token) {
      console.log('SessionsService: No token available, skipping load');
      return;
    }

    console.log('SessionsService: Starting to load sessions');
    this.isLoadingSignal.set(true);
    this.errorSignal.set(null);

    this.apiService.getSessions().subscribe({
      next: (response) => {
        console.log('SessionsService: Successfully loaded sessions:', response?.sessions?.length || 0);
        this.sessionsResponseSignal.set(response);
        this.isLoadingSignal.set(false);
        this.hasLoadedOnceSignal.set(true);
      },
      error: (error) => {
        console.error('SessionsService: Error loading sessions:', error);
        this.errorSignal.set(error.message || 'Failed to load sessions');
        this.isLoadingSignal.set(false);
      }
    });
  }


  constructor() {
    // Initialize previous token signal with current token
    const initialToken = this.authService.token();
    this.previousTokenSignal.set(initialToken);
    
    // Check if token is already available (e.g., on page refresh)
    if (initialToken && this.authService.status() === 'success') {
      console.log('SessionsService: Initial token found, loading sessions immediately');
      this.loadSessions();
    }

    // Wait for token to be available before loading sessions
    // Use effect to reactively load when token becomes available
    effect(() => {
      const token = this.authService.token();
      const status = this.authService.status();
      const previousToken = this.previousTokenSignal();
      
      // If token changed (new login), reset the loaded flag
      if (token !== previousToken) {
        this.previousTokenSignal.set(token);
        if (token) {
          // Token changed and exists - reset loaded flag to allow reload
          this.hasLoadedOnceSignal.set(false);
          this.sessionsResponseSignal.set(null);
        } else {
          // Token removed - clear sessions
          this.sessionsResponseSignal.set(null);
          this.hasLoadedOnceSignal.set(false);
        }
      }
      
      // Load if we have a token and status is success
      if (token && status === 'success' && !this.hasLoadedOnceSignal()) {
        console.log('SessionsService: Token available, loading sessions');
        this.loadSessions();
      }
    });
  }
}
