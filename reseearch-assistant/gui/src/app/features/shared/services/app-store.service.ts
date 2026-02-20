import { Injectable, signal, computed, effect } from '@angular/core';

interface AppStoreState {
  sidebarOpen: boolean;
  sizes: { left: number; right: number };
}

@Injectable({
  providedIn: 'root'
})
export class AppStoreService {
  private readonly STORAGE_KEY = 'vast-gui-app-store';

  // Initialize state from localStorage or defaults
  private state = signal<AppStoreState>({
    sidebarOpen: this.loadFromStorage().sidebarOpen ?? false,
    sizes: this.loadFromStorage().sizes ?? { left: 50, right: 50 },
  });

  // Computed signals for reactive access
  sidebarOpen = computed(() => this.state().sidebarOpen);
  sizes = computed(() => this.state().sizes);

  constructor() {
    // Save to localStorage whenever state changes
    effect(() => {
      const state = this.state();
      this.saveToStorage(state);
    });
  }

  toggleSidebar(): void {
    this.state.update(state => ({
      ...state,
      sidebarOpen: !state.sidebarOpen
    }));
  }

  closeSidebar(): void {
    this.state.update(state => ({
      ...state,
      sidebarOpen: false
    }));
  }

  setSizes(left: number, right: number): void {
    this.state.update(state => ({
      ...state,
      sizes: { left, right }
    }));
  }

  private loadFromStorage(): Partial<AppStoreState> {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  }

  private saveToStorage(state: AppStoreState): void {
    try {
      const dataToStore = {
        sidebarOpen: state.sidebarOpen,
        sizes: state.sizes,
      };
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(dataToStore));
    } catch {
      // Ignore storage errors
    }
  }
}