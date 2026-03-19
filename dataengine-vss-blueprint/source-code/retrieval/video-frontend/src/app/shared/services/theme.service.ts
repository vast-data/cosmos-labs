import { Injectable, signal, effect } from '@angular/core';

export type Theme = 'light' | 'dark';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly THEME_STORAGE_KEY = 'video-lab-theme';
  
  // Signal to track current theme
  private _theme = signal<Theme>(this.getInitialTheme());
  theme = this._theme.asReadonly();

  constructor() {
    // Apply theme whenever it changes
    effect(() => {
      const theme = this._theme();
      this.applyTheme(theme);
    });

    // Initialize theme on service creation
    this.applyTheme(this._theme());
  }

  private getInitialTheme(): Theme {
    // Check localStorage first
    const saved = localStorage.getItem(this.THEME_STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') {
      return saved;
    }
    // Default to dark theme
    return 'dark';
  }

  toggleTheme(): void {
    const currentTheme = this._theme();
    const newTheme: Theme = currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
  }

  setTheme(theme: Theme): void {
    this._theme.set(theme);
    localStorage.setItem(this.THEME_STORAGE_KEY, theme);
  }

  private applyTheme(theme: Theme): void {
    document.documentElement.setAttribute('data-theme', theme);
  }

  isDark(): boolean {
    return this._theme() === 'dark';
  }

  isLight(): boolean {
    return this._theme() === 'light';
  }
}

