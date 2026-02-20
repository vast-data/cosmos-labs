import { ChangeDetectionStrategy, Component } from '@angular/core';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-weather-date',
  standalone: true,
  imports: [DatePipe],
  template: `
    <div class="weather-date">
      <!-- Weather placeholder -->
      <div class="weather-date__weather">
        <div class="weather-date__icon">
          <div class="weather-date__sun"></div>
        </div>
        <span>Sunny outside</span>
      </div>
      
      <!-- Separator -->
      <span class="weather-date__separator">|</span>
      
      <!-- Current date -->
      <span>{{ formattedDate }}</span>
    </div>
  `,
  styles: [`
    .weather-date {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      color: rgba(255, 255, 255, 0.6);
      font-weight: 600;
      font-size: 1.125rem;

      &__weather {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      &__icon {
        width: 18px;
        height: 18px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      &__sun {
        width: 12px;
        height: 12px;
        border: 1px solid #EEEEEE;
        border-radius: 50%;
      }

      &__separator {
        color: rgba(255, 255, 255, 0.4);
      }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WeatherDateComponent {
  get formattedDate(): string {
    const now = new Date();
    const day = now.getDate();
    const month = now.toLocaleDateString('en-US', { month: 'short' });
    const year = now.getFullYear().toString().slice(-2);
    return `${day} ${month} ${year}`;
  }
}
