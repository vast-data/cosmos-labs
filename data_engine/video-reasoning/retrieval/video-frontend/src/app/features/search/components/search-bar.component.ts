import { Component, EventEmitter, Output, inject, ChangeDetectorRef, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { HttpClient } from '@angular/common/http';
import { SearchRequest } from '../../../shared/models/video.model';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatIconModule,
    MatSlideToggleModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatFormFieldModule,
    MatInputModule
  ],
  template: `
    <div class="search-bar-container">
      <form [formGroup]="searchForm" (ngSubmit)="onSearch()" class="search-form">
        
        <!-- Main Search Field - Native HTML -->
        <div class="custom-search-field">
          <div class="search-icon">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zM18 18l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <input 
            type="text"
            class="search-input"
            formControlName="query"
            [placeholder]="placeholderText">
          <button 
            type="button"
            class="clear-button"
            *ngIf="searchForm.get('query')?.value"
            (click)="clearSearch()">
            ✕
          </button>
        </div>

        <!-- Search Button -->
        <button 
          mat-raised-button 
          color="primary" 
          type="submit"
          class="search-button"
          [disabled]="!searchForm.get('query')?.value">
          <mat-icon>search</mat-icon>
          <span>Search</span>
        </button>
      </form>

      <!-- Video Scope Filter (below search bar) -->
      <div class="scope-filter">
        <label class="scope-label">Search in:</label>
        <div class="scope-pills">
          <button 
            type="button"
            class="scope-pill"
            [class.active]="searchForm.value.scope === 'all'"
            (click)="searchForm.patchValue({ scope: 'all' })">
            <mat-icon>public</mat-icon>
            <span>All Videos</span>
          </button>
          <button 
            type="button"
            class="scope-pill"
            [class.active]="searchForm.value.scope === 'mine'"
            (click)="searchForm.patchValue({ scope: 'mine' })">
            <mat-icon>person</mat-icon>
            <span>My Videos</span>
          </button>
          <button 
            type="button"
            class="scope-pill"
            [class.active]="searchForm.value.scope === 'public'"
            (click)="searchForm.patchValue({ scope: 'public' })">
            <mat-icon>visibility</mat-icon>
            <span>Public Only</span>
          </button>
        </div>
      </div>

      <!-- AI Enhancement Toggle (below search bar, inside form for binding) -->
      <form [formGroup]="searchForm">
        <div class="ai-toggle-container">
          <mat-slide-toggle 
            formControlName="useLlm"
            color="primary"
            class="ai-toggle">
            <div class="toggle-label">
              <mat-icon class="toggle-icon">auto_awesome</mat-icon>
              <span>Enable LLM Reasoning</span>
            </div>
          </mat-slide-toggle>
        </div>
      </form>

      <!-- Quick Suggestions -->
      <div class="search-hints" *ngIf="quickSuggestions.length > 0">
        <span class="hint-label">Try:</span>
        <div class="hint-chips">
          <button 
            type="button" 
            class="hint-chip" 
            *ngFor="let suggestion of quickSuggestions"
            (click)="setQuery(suggestion)">
            {{ suggestion }}
          </button>
        </div>
      </div>

      <!-- Time Selection Filter -->
      <div class="time-filter">
        <span class="time-label">Time Selection:</span>
        <div class="time-pills">
          <button 
            type="button"
            class="time-pill"
            [class.active]="searchForm.value.timeFilter === 'all'"
            (click)="selectTimeFilter('all')">
            <mat-icon>all_inclusive</mat-icon>
            <span>All Time</span>
          </button>
          <button 
            type="button"
            class="time-pill"
            [class.active]="searchForm.value.timeFilter === '5m'"
            (click)="selectTimeFilter('5m')">
            <mat-icon>schedule</mat-icon>
            <span>Last 5 min</span>
          </button>
          <button 
            type="button"
            class="time-pill"
            [class.active]="searchForm.value.timeFilter === '15m'"
            (click)="selectTimeFilter('15m')">
            <mat-icon>update</mat-icon>
            <span>Last 15 min</span>
          </button>
          <button 
            type="button"
            class="time-pill"
            [class.active]="searchForm.value.timeFilter === '1h'"
            (click)="selectTimeFilter('1h')">
            <mat-icon>access_time</mat-icon>
            <span>Last 1 hour</span>
          </button>
          <button 
            type="button"
            class="time-pill"
            [class.active]="searchForm.value.timeFilter === '24h'"
            (click)="selectTimeFilter('24h')">
            <mat-icon>today</mat-icon>
            <span>Last 24 hours</span>
          </button>
          <button 
            type="button"
            class="time-pill"
            [class.active]="searchForm.value.timeFilter === '7d'"
            (click)="selectTimeFilter('7d')">
            <mat-icon>date_range</mat-icon>
            <span>Last week</span>
          </button>
          <button 
            type="button"
            class="time-pill custom-pill"
            [class.active]="searchForm.value.timeFilter === 'custom'"
            (click)="selectCustomDate()">
            <mat-icon>event</mat-icon>
            <span>Custom Date</span>
          </button>
        </div>
      </div>

      <!-- Custom Date Range Picker (always rendered, show/hide with CSS) -->
      <form [formGroup]="searchForm">
        <div class="custom-date-picker" [class.visible]="showCustomDatePicker">
          <mat-form-field appearance="outline" class="date-field">
            <mat-label>Start Date</mat-label>
            <input 
              matInput 
              [matDatepicker]="startPicker"
              formControlName="customStartDate"
              placeholder="Select start date">
            <mat-datepicker-toggle matIconSuffix [for]="startPicker"></mat-datepicker-toggle>
            <mat-datepicker #startPicker></mat-datepicker>
          </mat-form-field>

          <mat-form-field appearance="outline" class="date-field">
            <mat-label>End Date</mat-label>
            <input 
              matInput 
              [matDatepicker]="endPicker"
              formControlName="customEndDate"
              placeholder="Select end date">
            <mat-datepicker-toggle matIconSuffix [for]="endPicker"></mat-datepicker-toggle>
            <mat-datepicker #endPicker></mat-datepicker>
          </mat-form-field>
        </div>
      </form>
    </div>
  `,
  styles: [`
    /* ============================================
       NATIVE HTML5 SEARCH BAR - CLEAN & STABLE
       ============================================ */
    
    /* Container */
    .search-bar-container {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 2rem;
      margin-bottom: 2rem;
    }

    /* Main Search Form */
    .search-form {
      display: flex;
      gap: 1rem;
      align-items: stretch;
      margin-bottom: 1.5rem;
    }

    /* ============================================
       NATIVE SEARCH INPUT FIELD
       ============================================ */
    .custom-search-field {
      flex: 1;
      position: relative;
      display: flex;
      align-items: center;
      background: rgba(255, 255, 255, 0.08);
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      padding: 0 1rem;
      transition: all 0.2s ease;
      
      &:focus-within {
        border-color: #0047AB; /* Darker space blue */
        background: rgba(255, 255, 255, 0.12);
        box-shadow: 0 0 0 3px rgba(0, 71, 171, 0.15);
      }
      
      .search-icon {
        color: rgba(0, 71, 171, 0.9); /* Darker space blue */
        display: flex;
        align-items: center;
        margin-right: 0.75rem;
        flex-shrink: 0;
      }
      
      .search-input {
        flex: 1;
        background: transparent;
        border: none;
        outline: none;
        color: #fff;
        font-size: 1rem;
        padding: 1rem 0;
        font-family: 'Roboto', sans-serif;
        
        &::placeholder {
          color: rgba(255, 255, 255, 0.65); /* Brighter gray */
        }
        
        &:focus {
          outline: none;
        }
      }
      
      .clear-button {
        background: rgba(255, 255, 255, 0.1);
        border: none;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: rgba(255, 255, 255, 0.7); /* Brighter */
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        flex-shrink: 0;
        margin-left: 0.5rem;
        
        &:hover {
          background: rgba(255, 255, 255, 0.2);
          color: #fff;
        }
      }
    }

    /* ============================================
       AI SEARCH BUTTON
       ============================================ */
    .search-button {
      height: auto;
      min-height: 56px;
      padding: 0 2rem;
      background: linear-gradient(135deg, #0047AB 0%, #002766 100%) !important; /* Darker space blues */
      border-radius: 8px !important;
      font-weight: 500;
      cursor: pointer !important;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      
      * {
        cursor: pointer !important;
      }
      
      &:disabled {
        opacity: 0.5;
        cursor: not-allowed !important;
        
        * {
          cursor: not-allowed !important;
        }
      }
      
      &:not(:disabled):hover {
        box-shadow: 0 4px 12px rgba(0, 71, 171, 0.6);
      }
    }

    /* ============================================
       VIDEO SCOPE FILTER (Pill-Style Toggle)
       ============================================ */
    .scope-filter {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.5rem;
      
      .scope-label {
        color: rgba(255, 255, 255, 0.85);
        font-size: 0.95rem;
        font-weight: 500;
      }
      
      .scope-pills {
        display: flex;
        gap: 0.5rem;
        background: rgba(0, 71, 171, 0.12);
        padding: 0.25rem;
        border-radius: 12px;
        border: 1px solid rgba(0, 71, 171, 0.3);
        
        .scope-pill {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.625rem 1.25rem;
          background: transparent;
          border: none;
          border-radius: 10px;
          color: rgba(255, 255, 255, 0.7);
          font-size: 0.9rem;
          font-weight: 500;
          font-family: 'Roboto', sans-serif;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          overflow: hidden;
          
          mat-icon {
            font-size: 1.25rem;
            width: 1.25rem;
            height: 1.25rem;
            transition: all 0.3s ease;
          }
          
          &:hover:not(.active) {
            background: rgba(0, 71, 171, 0.2);
            color: rgba(255, 255, 255, 0.9);
            transform: translateY(-1px);
          }
          
          &.active {
            background: linear-gradient(135deg, #0047AB 0%, #003380 100%);
            color: #ffffff;
            box-shadow: 
              0 4px 12px rgba(0, 71, 171, 0.4),
              inset 0 1px 0 rgba(255, 255, 255, 0.2);
            transform: translateY(0);
            
            mat-icon {
              color: #00d9ff;
              filter: drop-shadow(0 0 4px rgba(0, 217, 255, 0.6));
            }
          }
          
          &:active {
            transform: translateY(1px);
          }
        }
      }
    }

    /* ============================================
       AI ENHANCEMENT TOGGLE
       ============================================ */
    .ai-toggle-container {
      padding: 1rem 0;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      
      .ai-toggle {
        ::ng-deep .mdc-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .toggle-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: rgba(255, 255, 255, 0.9);
          font-size: 0.95rem;
          font-weight: 500;
          user-select: none;
          cursor: pointer;
          
          .toggle-icon {
            font-size: 20px;
            width: 20px;
            height: 20px;
            color: #00d9ff;
          }
        }
        
        ::ng-deep .mdc-switch {
          .mdc-switch__track {
            background: rgba(0, 71, 171, 0.3);
            border-color: rgba(0, 71, 171, 0.5);
          }
          
          &.mdc-switch--selected .mdc-switch__track {
            background: linear-gradient(135deg, #0047AB 0%, #003380 100%);
            border-color: #0047AB;
          }
          
          .mdc-switch__handle-track .mdc-switch__handle {
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
          }
          
          &.mdc-switch--selected .mdc-switch__handle {
            background: #00d9ff;
            box-shadow: 0 0 12px rgba(0, 217, 255, 0.6);
          }
        }
      }
    }

    /* ============================================
       SEARCH HINTS & SUGGESTIONS
       ============================================ */
    .search-hints {
      display: flex;
      align-items: flex-start;
      gap: 1rem;
      padding-top: 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      
      .hint-label {
        color: rgba(255, 255, 255, 0.85); /* Brighter gray */
        font-size: 0.9rem;
        font-weight: 500;
        padding-top: 0.5rem; /* Align with first row of chips */
        flex-shrink: 0;
      }
      
      .hint-chips {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        flex: 1;
        
        .hint-chip {
          background: rgba(0, 71, 171, 0.15); /* Darker space blue */
          color: rgba(255, 255, 255, 0.9); /* Brighter text */
          border: 1px solid rgba(0, 71, 171, 0.4);
          border-radius: 20px;
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
          font-family: 'Roboto', sans-serif;
          cursor: pointer;
          transition: all 0.2s ease;
          white-space: nowrap; /* Keep text on one line */
          
          &:hover {
            background: rgba(0, 71, 171, 0.25);
            border-color: rgba(0, 71, 171, 0.6);
            transform: translateY(-1px);
            color: #fff;
            box-shadow: 0 2px 8px rgba(0, 71, 171, 0.3);
          }
          
          &:active {
            transform: translateY(0);
          }
        }
      }
    }

    /* ============================================
       TIME SELECTION FILTER
       ============================================ */
    .time-filter {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1.25rem 0 0.5rem 0;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      margin-top: 1rem;
    }

    .time-label {
      font-size: 0.9rem;
      color: rgba(255, 255, 255, 0.7);
      font-weight: 500;
      white-space: nowrap;
    }

    .time-pills {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .time-pill {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.5rem 1rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 20px;
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.85rem;
      font-family: 'Roboto', sans-serif;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
      
      mat-icon {
        font-size: 1.1rem;
        width: 1.1rem;
        height: 1.1rem;
        color: rgba(0, 217, 255, 0.7);
      }
      
      &.active {
        background: linear-gradient(135deg, #0047AB 0%, #002766 100%);
        border-color: rgba(0, 71, 171, 0.8);
        color: #fff;
        box-shadow: 0 2px 12px rgba(0, 71, 171, 0.4);
        
        mat-icon {
          color: #00d9ff;
        }
      }
      
      &:hover:not(.active) {
        background: rgba(0, 71, 171, 0.15);
        border-color: rgba(0, 71, 171, 0.4);
        color: #fff;
        transform: translateY(-1px);
        
        mat-icon {
          color: #00d9ff;
        }
      }
      
      &:active {
        transform: translateY(0);
      }
      
      &.custom-pill {
        border: 2px dashed rgba(0, 217, 255, 0.3);
        
        &.active {
          border-style: solid;
          border-width: 1px;
        }
      }
    }

    /* ============================================
       CUSTOM DATE PICKER
       ============================================ */
    .custom-date-picker {
      display: none;
      gap: 1rem;
      margin-top: 1rem;
      padding: 1rem;
      background: rgba(0, 71, 171, 0.05);
      border: 1px solid rgba(0, 71, 171, 0.2);
      border-radius: 8px;
      opacity: 0;
      max-height: 0;
      overflow: hidden;
      transition: opacity 0.3s ease-out, max-height 0.3s ease-out, margin-top 0.3s ease-out, padding 0.3s ease-out;
      
      &.visible {
        display: flex;
        opacity: 1;
        max-height: 200px;
      }
    }

    .date-field {
      flex: 1;
      
      ::ng-deep {
        .mat-mdc-form-field {
          width: 100%;
        }
        
        .mat-mdc-text-field-wrapper {
          background: rgba(255, 255, 255, 0.08);
          border-radius: 8px;
        }
        
        .mdc-text-field {
          background: transparent !important;
        }
        
        .mat-mdc-form-field-focus-overlay {
          background: transparent;
        }
        
        .mdc-notched-outline__leading,
        .mdc-notched-outline__notch,
        .mdc-notched-outline__trailing {
          border-color: rgba(255, 255, 255, 0.2) !important;
        }
        
        .mat-mdc-form-field.mat-focused {
          .mdc-notched-outline__leading,
          .mdc-notched-outline__notch,
          .mdc-notched-outline__trailing {
            border-color: rgba(0, 217, 255, 0.6) !important;
          }
        }
        
        .mat-mdc-input-element {
          color: #fff;
          caret-color: #00d9ff;
        }
        
        .mat-mdc-form-field-label {
          color: rgba(255, 255, 255, 0.7) !important;
        }
        
        .mat-mdc-form-field.mat-focused .mat-mdc-form-field-label {
          color: rgba(0, 217, 255, 0.9) !important;
        }
        
        .mat-datepicker-toggle {
          color: rgba(0, 217, 255, 0.8);
        }
      }
    }
  `]
})
export class SearchBarComponent implements OnInit {
  fb = inject(FormBuilder);
  cdr = inject(ChangeDetectorRef);
  http = inject(HttpClient);
  @Output() search = new EventEmitter<SearchRequest>();

  showCustomDatePicker = false;
  placeholderText = 'Search videos...';
  quickSuggestions: string[] = [];

  searchForm = this.fb.group({
    query: [''],
    scope: ['all'], // 'all', 'mine', 'public'
    useLlm: [false], // AI enhancement toggle
    timeFilter: ['all'], // 'all', '5m', '15m', '1h', '24h', '7d', 'custom'
    customStartDate: [null as Date | null],
    customEndDate: [null as Date | null]
  });

  ngOnInit() {
    this.loadSearchSuggestions();
  }

  loadSearchSuggestions() {
    this.http.get<any>(`${environment.apiUrl}/frontend/search-suggestions`).subscribe({
      next: (config) => {
        if (config.placeholder_examples && config.placeholder_examples.length > 0) {
          this.placeholderText = `Search videos... (e.g., ${config.placeholder_examples.join(', ')})`;
        }
        if (config.quick_suggestions && config.quick_suggestions.length > 0) {
          this.quickSuggestions = config.quick_suggestions;
        }
      },
      error: (err) => {
        console.error('Failed to load search suggestions from backend, using defaults', err);
        // Keep defaults set in property initialization
      }
    });
  }

  selectTimeFilter(filter: string) {
    this.searchForm.patchValue({ timeFilter: filter });
    // Hide custom date picker if switching to a preset filter
    if (filter !== 'custom') {
      this.showCustomDatePicker = false;
      // Clear custom dates
      this.searchForm.patchValue({ 
        customStartDate: null, 
        customEndDate: null 
      });
    }
  }

  selectCustomDate() {
    this.searchForm.patchValue({ timeFilter: 'custom' });
    this.showCustomDatePicker = true;
  }

  onSearch() {
    const formValue = this.searchForm.value;
    if (!formValue.query) return;

    // Map scope to include_public flag
    // 'all' = show everything (public + mine)
    // 'mine' = show only mine (no public)
    // 'public' = show only public
    const includePublic = formValue.scope === 'all' || formValue.scope === 'public';

    console.log('[DEBUG] Form value:', formValue);
    console.log('[DEBUG] useLlm value:', formValue.useLlm);
    console.log('[DEBUG] timeFilter value:', formValue.timeFilter);

    const request: SearchRequest = {
      query: formValue.query,
      top_k: 15, // Fixed default
      tags: [], // Removed for now
      include_public: includePublic,
      use_llm: formValue.useLlm || false,
      time_filter: formValue.timeFilter || 'all'
    };

    // Add custom date range if 'custom' is selected
    if (formValue.timeFilter === 'custom') {
      if (formValue.customStartDate) {
        // Set start date to beginning of day (00:00:00) in UTC
        const startDate = new Date(formValue.customStartDate);
        startDate.setHours(0, 0, 0, 0);
        request.custom_start_date = startDate.toISOString();
        console.log('[DEBUG] Custom start date (UTC):', request.custom_start_date);
      }
      if (formValue.customEndDate) {
        // Set end date to end of day (23:59:59) in UTC
        const endDate = new Date(formValue.customEndDate);
        endDate.setHours(23, 59, 59, 999);
        request.custom_end_date = endDate.toISOString();
        console.log('[DEBUG] Custom end date (UTC):', request.custom_end_date);
      }
    }

    console.log('[DEBUG] Search request:', request);
    this.search.emit(request);
  }

  setQuery(query: string) {
    // Only populate the search bar, don't trigger search
    this.searchForm.patchValue({ query });
  }

  clearSearch() {
    this.searchForm.patchValue({ query: '' });
  }
}

