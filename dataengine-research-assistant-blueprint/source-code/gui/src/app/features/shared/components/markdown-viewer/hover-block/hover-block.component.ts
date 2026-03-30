import {
    Component,
    ElementRef,
    HostListener,
    inject,
    signal,
    computed, input
} from '@angular/core';
import { CommonModule } from '@angular/common'
import { MatIconModule } from '@angular/material/icon'
import { ReportPageStoreService } from '../../../../reports/services/report-page-store.service';

@Component({
    selector: 'app-hover-block',
    standalone: true,
    imports: [CommonModule, MatIconModule],
    template: `
        <button
            class="icon-button"
            (click)="toggleMenu($event)"
        >
            <mat-icon>more_vert</mat-icon>
        </button>

        <div
            class="custom-menu"
            *ngIf="menuVisible()"
            (mouseenter)="menuHovering = true"
            (mouseleave)="onMenuLeave()"
        >
            <!-- <div class="menu-item" (click)="addMoreSection()">Place greater emphasis on this section</div>
            <div class="menu-item" (click)="changeToneSection()">Change the tone of this section</div>
            <div class="menu-item" (click)="rewordToneSection()">Reword the entire section</div>
            <div class="menu-item" (click)="removeSection()">Remove this section</div> -->
        </div>

        <ng-content></ng-content>
    `,
    styles: [`
        :host {
            position: relative;
            display: block;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
            background: transparent;
            transition: background-color 0.2s ease;

            &:hover {
                .icon-button {
                  display: flex;
                }
            }
        }

        @supports (background: color(display-p3 0.1216 0.1725 0.2784)) {
            :host(:hover) {
                background: color(display-p3 0.1216 0.1725 0.2784);
            }
        }

        @supports not (background: color(display-p3 0.1216 0.1725 0.2784)) {
            :host(:hover) {
                background: #1B2C49;
            }
        }

        .icon-button {
            display: none;
            position: absolute;
            top: 8px;
            right: 8px;
            background: transparent;
            border: none;
            cursor: pointer;
            padding: 4px;
            z-index: 10;
            align-items: center;
            justify-content: center;
        }

        mat-icon {
            color: white;
        }

        .custom-menu {
            position: absolute;
            top: 36px;
            right: 8px;
            background: #1e2a3a;
            border: 1px solid #2a3d5c;
            border-radius: 4px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 20;
            min-width: 120px;
            padding: 4px 0;
        }

        .menu-item {
            padding: 8px 12px;
            color: white;
            cursor: pointer;
        }

        .menu-item:hover {
            background-color: #2a3d5c;
        }
    `],
})
export class HoverBlockComponent {
    private readonly isInside = signal(false)
    private readonly manuallyOpen = signal(false)

    // Показываем меню, если либо вручную открыто, либо курсор в меню
    readonly menuVisible = computed(() => this.manuallyOpen() || this.isInside())

    originalcontent = input('')
    menuHovering = false

    private host = inject(ElementRef<HTMLElement>)
    private reportStore = inject(ReportPageStoreService)

    toggleMenu(event: MouseEvent) {
        event.stopPropagation()
        this.manuallyOpen.set(!this.manuallyOpen())
        console.log(this.originalcontent());
    }

    @HostListener('document:click')
    onClickOutside() {
        this.manuallyOpen.set(false)
    }

    onMenuLeave() {
        // задержка, чтобы не пропадало при переходе
        setTimeout(() => {
            if (!this.menuHovering) {
                this.manuallyOpen.set(false)
                this.isInside.set(false)
            }
        }, 150)
    }

    copy() {
        console.log('Copy clicked')
        this.closeMenu()
    }

    bookmark() {
        console.log('Bookmark clicked')
        this.closeMenu()
    }

    share() {
        console.log('Share clicked')
        this.closeMenu()
    }

    // removeSection() {
    //     this.reportStore.sendMessage(
    //         'ReportMode. Remove this section: \n ' + this.originalcontent,
    //         true,
    //     )
    //     this.closeMenu();
    // }

    // addMoreSection() {
    //     this.reportStore.sendMessage(
    //         'ReportMode. Place greater emphasis on this section: \n ' + this.originalcontent,
    //         true,
    //     )
    //     this.closeMenu();
    // }

    // changeToneSection() {
    //     this.reportStore.sendMessage(
    //         'ReportMode. Change the tone of this section: \n ' + this.originalcontent,
    //         true,
    //     )
    //     this.closeMenu();
    // }

    // rewordToneSection() {
    //     this.reportStore.sendMessage(
    //         'ReportMode. Reword the entire section: \n ' + this.originalcontent,
    //         true,
    //     )
    //     this.closeMenu();
    // }

    private closeMenu() {
        this.manuallyOpen.set(false)
        this.isInside.set(false)
    }
}
