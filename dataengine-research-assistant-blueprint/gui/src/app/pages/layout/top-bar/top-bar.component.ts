import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatIcon } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { UserLogoComponent } from '../../../features/shared/components/user-logo/user-logo.component';
import { AppStoreService } from '../../../features/shared/services/app-store.service';

@Component({
  selector: 'app-top-bar',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatIcon,
    MatTooltipModule,
    UserLogoComponent,
  ],
  templateUrl: './top-bar.component.html',
  styleUrl: './top-bar.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TopBarComponent {
  private appStoreService = inject(AppStoreService);

  toggleSidebar(): void {
    this.appStoreService.toggleSidebar();
  }

  onLogoClick(): void {
    this.appStoreService.closeSidebar();
  }
}