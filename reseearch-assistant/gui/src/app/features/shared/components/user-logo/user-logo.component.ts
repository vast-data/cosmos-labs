import { ChangeDetectionStrategy, Component, computed, inject, Input } from '@angular/core';
import { AuthService } from '../../../auth/services/auth.service';
import { MatMenu, MatMenuTrigger } from '@angular/material/menu';

@Component({
    selector: 'app-user-logo',
    standalone: true,
    imports: [
        MatMenuTrigger,
        MatMenu
    ],
    templateUrl: './user-logo.component.html',
    styleUrl: './user-logo.component.scss',
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class UserLogoComponent {
    authService = inject(AuthService);

    @Input() size = 56;
    @Input() withMenu = false;

    name = computed(() => {
        return this.authService.user();
    })

    firstChar = computed(() => {
        return this.name()?.charAt(0).toUpperCase();
    });

    logout() {
        this.authService.logout();
    }
}
