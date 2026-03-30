import { Injectable, inject, signal, computed, effect } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { SETTINGS } from '../settings';

const STORAGE_KEY = 'vastrag_prompt_state';

interface PromptPersistence {
  deepResearchEnabled: boolean;
  customSystemPrompt: string | null;
}

@Injectable({ providedIn: 'root' })
export class SystemPromptService {
  private http = inject(HttpClient);

  defaultSystemPrompt = signal('');
  deepResearchPrompt = signal('');
  customSystemPrompt = signal('');
  deepResearchEnabled = signal(false);
  loaded = signal(false);

  hasCustomPrompt = computed(() => this.customSystemPrompt() !== this.defaultSystemPrompt());

  constructor() {
    effect(() => {
      if (!this.loaded()) return;
      const state: PromptPersistence = {
        deepResearchEnabled: this.deepResearchEnabled(),
        customSystemPrompt: this.customSystemPrompt(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    });
  }

  loadSystemPrompt(): void {
    if (this.loaded()) return;
    this.http.get<{ system_prompt: string; deep_research_prompt?: string }>(`${SETTINGS.BASE_API_URL}/system-prompt`).subscribe({
      next: (response) => {
        this.defaultSystemPrompt.set(response.system_prompt);
        if (response.deep_research_prompt) {
          this.deepResearchPrompt.set(response.deep_research_prompt);
        }

        const saved = this.loadFromStorage();
        if (saved) {
          this.deepResearchEnabled.set(saved.deepResearchEnabled);
          if (saved.customSystemPrompt) {
            this.customSystemPrompt.set(saved.customSystemPrompt);
          } else if (saved.deepResearchEnabled && response.deep_research_prompt) {
            this.customSystemPrompt.set(response.deep_research_prompt);
          } else {
            this.customSystemPrompt.set(response.system_prompt);
          }
        } else {
          this.customSystemPrompt.set(response.system_prompt);
        }

        this.loaded.set(true);
      },
      error: (err) => console.error('Failed to load system prompt:', err)
    });
  }

  private loadFromStorage(): PromptPersistence | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  toggleDeepResearch(): void {
    const enabling = !this.deepResearchEnabled();
    this.deepResearchEnabled.set(enabling);
    if (enabling) {
      this.customSystemPrompt.set(this.deepResearchPrompt());
    } else {
      this.customSystemPrompt.set(this.defaultSystemPrompt());
    }
  }

  savePrompt(prompt: string): void {
    this.customSystemPrompt.set(prompt);
  }

  resetPrompt(): void {
    if (this.deepResearchEnabled()) {
      this.customSystemPrompt.set(this.deepResearchPrompt());
    } else {
      this.customSystemPrompt.set(this.defaultSystemPrompt());
    }
  }

  getEffectivePrompt(): string | null {
    if (this.deepResearchEnabled()) {
      return this.customSystemPrompt();
    }
    return this.hasCustomPrompt() ? this.customSystemPrompt() : null;
  }
}
