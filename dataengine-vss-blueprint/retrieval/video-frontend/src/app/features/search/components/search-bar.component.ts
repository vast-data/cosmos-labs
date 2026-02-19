import { Component, EventEmitter, Output, inject, ChangeDetectorRef, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { HttpClient } from '@angular/common/http';
import { SearchRequest, MetadataField, MetadataSchema } from '../../../shared/models/video.model';
import { environment } from '../../../../environments/environment';
import { SYSTEM_PROMPT_STORAGE_KEY, DEFAULT_SYSTEM_PROMPT } from '../../../features/settings/system-prompt-dialog.component';
import { getLLMSettings } from '../../../features/settings/advanced-llm-settings-dialog.component';
import { SearchService } from '../services/search.service';
import { SqlQueryDialogComponent } from './sql-query-dialog.component';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatSlideToggleModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatCheckboxModule,
    MatTooltipModule
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
              <span>Enable LLM Response</span>
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

      <!-- Custom Date & Time Range Picker (always rendered, show/hide with CSS) -->
      <form [formGroup]="searchForm">
        <div class="custom-date-picker" [class.visible]="showCustomDatePicker">
          <div class="datetime-group">
            <span class="datetime-label">From:</span>
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
            <mat-form-field appearance="outline" class="time-field">
              <mat-label>Start Time</mat-label>
              <input 
                matInput 
                type="time"
                formControlName="customStartTime"
                placeholder="00:00"
                #startTimeInput>
              <mat-icon matSuffix (click)="openTimePicker(startTimeInput)" class="time-picker-icon">schedule</mat-icon>
            </mat-form-field>
          </div>

          <div class="datetime-group">
            <span class="datetime-label">To:</span>
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
            <mat-form-field appearance="outline" class="time-field">
              <mat-label>End Time</mat-label>
              <input 
                matInput 
                type="time"
                formControlName="customEndTime"
                placeholder="23:59"
                #endTimeInput>
              <mat-icon matSuffix (click)="openTimePicker(endTimeInput)" class="time-picker-icon">schedule</mat-icon>
            </mat-form-field>
          </div>
        </div>
      </form>

      <!-- Advanced Filters Toggle -->
      <div class="advanced-filters-toggle">
        <button 
          type="button"
          class="toggle-button"
          (click)="toggleAdvancedFilters()"
          matTooltip="Discover and filter by additional metadata fields">
          <mat-icon>{{showAdvancedFilters() ? 'expand_less' : 'filter_list'}}</mat-icon>
          <span>{{showAdvancedFilters() ? 'Hide Filters' : 'Discover Metadata Filters'}}</span>
        </button>
        <button 
          type="button"
          class="toggle-button reveal-query-button"
          (click)="revealQuery()"
          [disabled]="!canRevealQuery()"
          matTooltip="Show the SQL query executed for similarity search">
          <mat-icon>code</mat-icon>
          <span>Reveal Similarity Query</span>
        </button>
        @if (loadingSchema()) {
          <span class="loading-indicator">Loading schema...</span>
        }
      </div>

      <!-- Dynamic Advanced Filters Panel -->
      @if (showAdvancedFilters() && metadataFields().length > 0) {
        <div class="advanced-filters-panel">
          <div class="filters-header">
            <span>Filter by metadata:</span>
            <button 
              type="button"
              class="clear-filters-btn"
              (click)="clearMetadataFilters()"
              *ngIf="hasActiveFilters()">
              <mat-icon>clear_all</mat-icon>
              Clear Filters
            </button>
          </div>
          <div class="filters-grid">
            @for (field of metadataFields(); track field.name) {
              <div class="filter-field">
                @if (field.ui_type === 'select' && field.options && field.options.length > 0) {
                  <!-- Select Dropdown -->
                  <mat-form-field appearance="outline" class="filter-input">
                    <mat-label>{{field.label}}</mat-label>
                    <mat-select 
                      [(ngModel)]="metadataFilterValues[field.name]"
                      (selectionChange)="onMetadataFilterChange()">
                      <mat-option [value]="">-- All --</mat-option>
                      @for (option of field.options; track option) {
                        <mat-option [value]="option">{{option}}</mat-option>
                      }
                    </mat-select>
                  </mat-form-field>
                } @else if (field.ui_type === 'text' || field.ui_type === 'select') {
                  <!-- Text Input -->
                  <mat-form-field appearance="outline" class="filter-input">
                    <mat-label>{{field.label}}</mat-label>
                    <input 
                      matInput 
                      [(ngModel)]="metadataFilterValues[field.name]"
                      (ngModelChange)="onMetadataFilterChange()"
                      [placeholder]="'Filter by ' + field.label.toLowerCase()">
                  </mat-form-field>
                } @else if (field.ui_type === 'checkbox') {
                  <!-- Checkbox -->
                  <mat-checkbox 
                    [(ngModel)]="metadataFilterValues[field.name]"
                    (ngModelChange)="onMetadataFilterChange()"
                    class="filter-checkbox">
                    {{field.label}}
                  </mat-checkbox>
                } @else if (field.ui_type === 'number') {
                  <!-- Number Input -->
                  <mat-form-field appearance="outline" class="filter-input">
                    <mat-label>{{field.label}}</mat-label>
                    <input 
                      matInput 
                      type="number"
                      [(ngModel)]="metadataFilterValues[field.name]"
                      (ngModelChange)="onMetadataFilterChange()"
                      [placeholder]="field.label">
                  </mat-form-field>
                }
              </div>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    /* ============================================
       NATIVE HTML5 SEARCH BAR - CLEAN & STABLE
       ============================================ */
    
    /* Container */
    .search-bar-container {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 2rem;
      margin-bottom: 2rem;
      transition: background 0.3s ease, border-color 0.3s ease;
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
      background: var(--bg-secondary);
      border: 2px solid var(--border-color);
      border-radius: 8px;
      padding: 0 1rem;
      transition: all 0.2s ease;
      
      &:focus-within {
        border-color: var(--accent-primary);
        background: var(--bg-card-hover);
        box-shadow: 0 0 0 3px rgba(115, 200, 253, 0.2); /* lightblue-400 with opacity */
      }
      
      .search-icon {
        color: var(--accent-primary); /* lightblue-400 */
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
        color: var(--text-primary);
        font-size: 1rem;
        padding: 1rem 0;
        font-family: 'Roboto', sans-serif;
        transition: color 0.3s ease;
        
        &::placeholder {
          color: var(--text-muted);
        }
        
        &:focus {
          outline: none;
        }
      }
      
      .clear-button {
        background: var(--bg-card);
        border: none;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-secondary);
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        flex-shrink: 0;
        margin-left: 0.5rem;
        
        &:hover {
          background: var(--bg-card-hover);
          color: var(--text-primary);
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
      background: var(--button-bg-primary) !important;
      color: var(--button-text) !important;
      border-radius: 8px !important;
      font-weight: 500;
      cursor: pointer !important;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.3s ease;
      
      * {
        cursor: pointer !important;
        color: var(--button-text) !important;
      }
      
      &:disabled {
        opacity: 0.5;
        cursor: not-allowed !important;
        
        * {
          cursor: not-allowed !important;
        }
      }
      
      &:not(:disabled):hover {
        background: var(--button-bg-hover) !important;
        box-shadow: var(--shadow-hover);
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
        color: var(--text-secondary);
        font-size: 0.95rem;
        font-weight: 500;
      }
      
      .scope-pills {
        display: flex;
        gap: 0.5rem;
        background: var(--bg-secondary);
        padding: 0.25rem;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        transition: background 0.3s ease, border-color 0.3s ease;
        
        .scope-pill {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.625rem 1.25rem;
          background: transparent;
          border: none;
          border-radius: 10px;
          color: var(--text-secondary);
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
            background: var(--bg-card-hover);
            color: var(--text-primary);
            transform: translateY(-1px);
          }
          
          &.active {
            background: var(--color-lightblue-400); /* lightblue-400 - active tab background */
            color: var(--color-blue-1000); /* blue-1000 - active tab text */
            box-shadow: var(--shadow);
            transform: translateY(0);
            
            mat-icon {
              color: var(--color-blue-1000); /* blue-1000 - icon matches text */
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
      border-top: 1px solid var(--border-color);
      transition: border-color 0.3s ease;
      
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
          color: var(--text-primary);
          font-size: 0.95rem;
          font-weight: 500;
          user-select: none;
          cursor: pointer;
          
          .toggle-icon {
            font-size: 20px;
            width: 20px;
            height: 20px;
            color: var(--accent-primary);
          }
        }
        
        ::ng-deep .mdc-switch {
          .mdc-switch__track {
            background: rgba(162, 174, 180, 0.3); /* gray-400 with opacity */
            border-color: rgba(162, 174, 180, 0.5); /* gray-400 with opacity */
          }
          
          &.mdc-switch--selected .mdc-switch__track {
            background: var(--color-lightblue-400); /* lightblue-400 */
            border-color: var(--color-lightblue-400);
          }
          
          .mdc-switch__handle-track .mdc-switch__handle {
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
          }
          
          &.mdc-switch--selected .mdc-switch__handle {
            background: var(--color-blue-1000); /* blue-1000 - dark handle on selected */
            box-shadow: 0 0 12px rgba(115, 200, 253, 0.6); /* lightblue-400 glow */
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
      border-top: 1px solid var(--border-color);
      transition: border-color 0.3s ease;
      
      .hint-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 500;
        padding-top: 0.5rem;
        flex-shrink: 0;
      }
      
      .hint-chips {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        flex: 1;
        
        .hint-chip {
          background: var(--bg-secondary);
          color: var(--text-primary);
          border: 1px solid var(--border-color);
          border-radius: 20px;
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
          font-family: 'Roboto', sans-serif;
          cursor: pointer;
          transition: all 0.2s ease;
          white-space: nowrap;
          
          &:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-hover);
            transform: translateY(-1px);
            color: var(--text-primary);
            box-shadow: var(--shadow);
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
      border-top: 1px solid var(--border-color);
      margin-top: 1rem;
      transition: border-color 0.3s ease;
    }

    .time-label {
      font-size: 0.9rem;
      color: var(--text-secondary);
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
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 20px;
      color: var(--text-secondary);
      font-size: 0.85rem;
      font-family: 'Roboto', sans-serif;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
      
      mat-icon {
        font-size: 1.1rem;
        width: 1.1rem;
        height: 1.1rem;
        color: var(--accent-primary);
      }
      
      &.active {
        background: var(--color-lightblue-400); /* lightblue-400 - active tab background */
        border-color: var(--color-lightblue-400); /* lightblue-400 - border matches background */
        color: var(--color-blue-1000); /* blue-1000 - active tab text */
        box-shadow: var(--shadow);
        
        mat-icon {
          color: var(--color-blue-1000); /* blue-1000 - icon matches text */
        }
      }
      
      &:hover:not(.active) {
        background: var(--bg-card-hover);
        border-color: var(--border-hover);
        color: var(--text-primary);
        transform: translateY(-1px);
        
        mat-icon {
          color: var(--accent-primary);
        }
      }
      
      &:hover.active {
        background: var(--button-bg-hover);
      }
      
      &:active {
        transform: translateY(0);
      }
      
      &.custom-pill {
        border: 2px dashed var(--accent-primary);
        
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
      flex-direction: column;
      gap: 1rem;
      margin-top: 1rem;
      padding: 1.25rem;
      background: rgba(115, 200, 253, 0.05); /* lightblue-400 with low opacity */
      border: 1px solid rgba(115, 200, 253, 0.2); /* lightblue-400 with opacity */
      border-radius: 8px;
      opacity: 0;
      max-height: 0;
      overflow: hidden;
      transition: opacity 0.3s ease-out, max-height 0.3s ease-out, margin-top 0.3s ease-out, padding 0.3s ease-out;
      
      &.visible {
        display: flex;
        opacity: 1;
        max-height: 300px;
      }
    }

    .datetime-group {
      display: flex;
      align-items: center;
      gap: 1rem;
      
      .datetime-label {
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 0.9rem;
        min-width: 45px;
      }
    }

    .date-field {
      flex: 1.5;
      
      ::ng-deep {
        .mat-mdc-form-field {
          width: 100%;
        }
        
        .mat-mdc-text-field-wrapper {
          background: var(--bg-secondary);
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
          border-color: var(--border-color) !important;
        }
        
        .mat-mdc-form-field.mat-focused {
          .mdc-notched-outline__leading,
          .mdc-notched-outline__notch,
          .mdc-notched-outline__trailing {
            border-color: var(--accent-primary) !important;
          }
        }
        
        .mat-mdc-input-element {
          color: var(--text-primary);
          caret-color: var(--accent-primary);
        }
        
        .mat-mdc-form-field-label {
          color: var(--text-secondary) !important;
        }
        
        .mat-mdc-form-field.mat-focused .mat-mdc-form-field-label {
          color: var(--accent-primary) !important;
        }
        
        .mat-datepicker-toggle {
          color: var(--accent-primary);
        }
      }
    }

    .time-field {
      flex: 1;
      
      ::ng-deep {
        .mat-mdc-form-field {
          width: 100%;
        }
        
        .mat-mdc-text-field-wrapper {
          background: var(--bg-secondary);
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
          border-color: var(--border-color) !important;
        }
        
        .mat-mdc-form-field.mat-focused {
          .mdc-notched-outline__leading,
          .mdc-notched-outline__notch,
          .mdc-notched-outline__trailing {
            border-color: var(--accent-primary) !important;
          }
        }
        
        .mat-mdc-input-element {
          color: var(--text-primary);
          caret-color: var(--accent-primary);
        }
        
        .mat-mdc-form-field-label {
          color: var(--text-secondary) !important;
        }
        
        .mat-mdc-form-field.mat-focused .mat-mdc-form-field-label {
          color: var(--accent-primary) !important;
        }
        
        .mat-icon {
          color: var(--accent-primary);
        }
        
        .time-picker-icon {
          cursor: pointer;
          transition: all 0.2s ease;
          
          &:hover {
            color: var(--accent-primary);
            transform: scale(1.1);
          }
          
          &:active {
            transform: scale(0.95);
          }
        }
      }
    }

    /* ============================================
       ADVANCED FILTERS SECTION
       ============================================ */
    .advanced-filters-toggle {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border-color);
      transition: border-color 0.3s ease;
      
      .toggle-button {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.75rem 1.25rem;
        color: var(--text-primary);
        font-size: 0.95rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        
        &:hover:not(:disabled) {
          background: var(--bg-card-hover);
          border-color: var(--border-hover);
        }
        
        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        mat-icon {
          font-size: 20px;
          width: 20px;
          height: 20px;
        }
      }

      .reveal-query-button {
        margin-left: 0.5rem;
      }
      
      .loading-indicator {
        color: var(--text-muted);
        font-size: 0.875rem;
        font-style: italic;
      }
    }

    .advanced-filters-panel {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 1.5rem;
      margin-top: 1rem;
      animation: slideDown 0.3s ease-out;
      transition: background 0.3s ease, border-color 0.3s ease;
      
      @keyframes slideDown {
        from {
          opacity: 0;
          transform: translateY(-10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      
      .filters-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-color);
        transition: border-color 0.3s ease;
        
        span {
          color: var(--text-primary);
          font-size: 1rem;
          font-weight: 500;
        }
        
        .clear-filters-btn {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          background: rgba(220, 38, 38, 0.2);
          border: 1px solid var(--accent-danger);
          border-radius: 6px;
          padding: 0.5rem 1rem;
          color: var(--text-primary);
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s ease;
          
          &:hover {
            background: rgba(220, 38, 38, 0.3);
            border-color: var(--accent-danger);
          }
          
          mat-icon {
            font-size: 18px;
            width: 18px;
            height: 18px;
          }
        }
      }
      
      .filters-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 1rem;
        
        .filter-field {
          .filter-input {
            width: 100%;
            
            ::ng-deep {
              .mat-mdc-text-field-wrapper {
                background: var(--bg-secondary);
              }
              
              .mat-mdc-form-field-focus-overlay {
                background: transparent;
              }
              
              .mdc-text-field--outlined .mdc-notched-outline .mdc-notched-outline__leading,
              .mdc-text-field--outlined .mdc-notched-outline .mdc-notched-outline__notch,
              .mdc-text-field--outlined .mdc-notched-outline .mdc-notched-outline__trailing {
                border-color: var(--border-color);
              }
              
              .mat-mdc-form-field.mat-focused .mdc-notched-outline .mdc-notched-outline__leading,
              .mat-mdc-form-field.mat-focused .mdc-notched-outline .mdc-notched-outline__notch,
              .mat-mdc-form-field.mat-focused .mdc-notched-outline .mdc-notched-outline__trailing {
                border-color: var(--accent-secondary) !important;
              }
              
              .mat-mdc-form-field-label {
                color: var(--text-secondary);
              }
              
              .mat-mdc-input-element {
                color: var(--text-primary);
              }
              
              .mat-mdc-select-value {
                color: var(--text-primary);
              }
              
              .mat-mdc-select-arrow {
                color: var(--text-secondary);
              }
            }
          }
          
          .filter-checkbox {
            ::ng-deep {
              .mdc-checkbox__background {
                border-color: var(--border-color);
              }
              
              .mdc-checkbox--selected .mdc-checkbox__background {
                background-color: var(--accent-secondary);
                border-color: var(--accent-secondary);
              }
              
              .mdc-label {
                color: var(--text-primary);
              }
            }
          }
        }
      }
    }
  `]
})
export class SearchBarComponent implements OnInit {
  fb = inject(FormBuilder);
  cdr = inject(ChangeDetectorRef);
  http = inject(HttpClient);
  dialog = inject(MatDialog);
  searchService = inject(SearchService);
  @Output() search = new EventEmitter<SearchRequest>();

  showCustomDatePicker = false;
  placeholderText = 'Search videos...';
  quickSuggestions: string[] = [];

  // Advanced Filters state
  showAdvancedFilters = signal(false);
  metadataFields = signal<MetadataField[]>([]);
  loadingSchema = signal(false);
  metadataFilterValues: Record<string, any> = {};

  searchForm = this.fb.group({
    query: [''],
    scope: ['all'], // 'all', 'mine', 'public'
    useLlm: [false], // AI enhancement toggle
    timeFilter: ['all'], // 'all', '5m', '15m', '1h', '24h', '7d', 'custom'
    customStartDate: [null as Date | null],
    customStartTime: ['00:00'],  // Default to start of day
    customEndDate: [null as Date | null],
    customEndTime: ['23:59']     // Default to end of day
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
      // Clear custom dates and reset times to defaults
      this.searchForm.patchValue({ 
        customStartDate: null, 
        customStartTime: '00:00',
        customEndDate: null,
        customEndTime: '23:59'
      });
    }
  }

  openTimePicker(inputElement: HTMLInputElement) {
    // Focus and click the input to open the native time picker
    inputElement.focus();
    inputElement.click();
    // For some browsers, we need to show the picker explicitly
    if (inputElement.showPicker) {
      inputElement.showPicker();
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

    const llmSettings = getLLMSettings();

    const request: SearchRequest = {
      query: formValue.query,
      top_k: llmSettings.searchTopK,
      tags: [], // Removed for now
      include_public: includePublic,
      use_llm: formValue.useLlm || false,
      time_filter: formValue.timeFilter || 'all',
      min_similarity: llmSettings.minSimilarityScore,
      llm_top_n: llmSettings.llmTopNSummaries
    };

    if (request.use_llm) {
      const storedPrompt = localStorage.getItem(SYSTEM_PROMPT_STORAGE_KEY);
      request.system_prompt = (storedPrompt && storedPrompt.trim()) ? storedPrompt.trim() : DEFAULT_SYSTEM_PROMPT;
    }

    // Custom date range (sent as local time to match VastDB timestamps)
    if (formValue.timeFilter === 'custom') {
      if (formValue.customStartDate) {
        const startDate = new Date(formValue.customStartDate);
        const [startHours, startMins] = (formValue.customStartTime || '00:00').split(':').map(Number);
        startDate.setHours(startHours, startMins, 0, 0);
        request.custom_start_date = this.formatLocalDateTime(startDate);
      }
      if (formValue.customEndDate) {
        const endDate = new Date(formValue.customEndDate);
        const [endHours, endMins] = (formValue.customEndTime || '23:59').split(':').map(Number);
        endDate.setHours(endHours, endMins, 59, 999);
        request.custom_end_date = this.formatLocalDateTime(endDate);
      }
    }

    // Add metadata filters if any are active
    if (this.hasActiveFilters()) {
      const activeFilters: Record<string, any> = {};
      for (const [key, value] of Object.entries(this.metadataFilterValues)) {
        if (value !== null && value !== undefined && value !== '') {
          activeFilters[key] = value;
        }
      }
      request.metadata_filters = activeFilters;
    }

    this.search.emit(request);
  }

  setQuery(query: string) {
    // Only populate the search bar, don't trigger search
    this.searchForm.patchValue({ query });
  }

  clearSearch() {
    this.searchForm.patchValue({ query: '' });
  }

  // Advanced Filters methods
  toggleAdvancedFilters() {
    const newState = !this.showAdvancedFilters();
    this.showAdvancedFilters.set(newState);
    
    // Load schema when opening for the first time
    if (newState && this.metadataFields().length === 0) {
      this.loadMetadataSchema();
    }
  }

  loadMetadataSchema() {
    this.loadingSchema.set(true);
    this.http.get<MetadataSchema>(`${environment.apiUrl}/metadata/schema`).subscribe({
      next: (schema) => {
        this.metadataFields.set(schema.schema);
        this.loadingSchema.set(false);
        console.log('[METADATA] Loaded schema:', schema);
      },
      error: (err) => {
        console.error('[METADATA] Failed to load schema:', err);
        this.loadingSchema.set(false);
      }
    });
  }

  onMetadataFilterChange() {
    // Filters are applied when user clicks search
    console.log('[METADATA] Filters changed:', this.metadataFilterValues);
  }

  clearMetadataFilters() {
    this.metadataFilterValues = {};
    console.log('[METADATA] Filters cleared');
  }

  hasActiveFilters(): boolean {
    return Object.values(this.metadataFilterValues).some(v => v !== null && v !== undefined && v !== '');
  }

  canRevealQuery(): boolean {
    const state = this.searchService.state();
    return !state.loading && state.sqlQuery !== null && state.sqlQuery !== undefined && state.sqlQuery.length > 0;
  }

  revealQuery() {
    const state = this.searchService.state();
    if (state.sqlQuery) {
      this.dialog.open(SqlQueryDialogComponent, {
        width: '800px',
        maxHeight: '85vh',
        panelClass: 'sql-query-dialog-container',
        disableClose: false,
        data: {
          sqlQuery: state.sqlQuery,
          userQuery: state.query
        }
      });
    }
  }

  /**
   * Format a Date as a local datetime string WITHOUT timezone conversion
   * Returns format: YYYY-MM-DDTHH:mm:ss (no 'Z' suffix)
   * This ensures the time matches what's stored in VastDB
   */
  private formatLocalDateTime(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
  }
}

