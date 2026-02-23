import { Component, computed, input, Signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIcon } from '@angular/material/icon';

@Component({
    selector: 'app-source-list',
    standalone: true,
    imports: [CommonModule, MatIcon],
    template: `
    <div class="source-list">
        @for (source of parsedSource(); track source.title) {
            <a
                class="chip"
                [href]="source.url"
                target="_blank"
                rel="noopener"
            >
                <mat-icon svgIcon="resource"></mat-icon>
                {{ source.title }}
            </a>
        }
    </div>
  `,
    styles: [`
        mat-icon {
            width: .7rem;
            height: 1rem;
            font-size: .7rem;
        }

    .source-list {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      padding: 8px 0;

        font-size: .8125rem;
        font-style: normal;
        font-weight: 600;
        line-height: .875rem;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px;
      border: 1px solid #343E55;
      border-radius: 8px;
      color: #d3dce6;
      text-decoration: none;
      background-color: rgba(255, 255, 255, 0.05);
      transition: background-color 0.2s ease, border-color 0.2s ease;
    }

    .chip:hover {
      background-color: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.4);
    }

    .icon {
      flex-shrink: 0;
      stroke: #d3dce6;
    }
  `]
})
export class SourceListComponent {
    sources = input('');
    parsedSource: Signal<any> = computed(() => {
        try {
            console.log(this.sources, JSON.parse(this.sources()));
            return JSON.parse(this.sources());
        } catch (e: any) {
            return [];
        }
    })
}
