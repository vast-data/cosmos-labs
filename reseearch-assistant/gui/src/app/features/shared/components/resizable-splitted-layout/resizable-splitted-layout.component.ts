import {
    AfterViewInit,
    ChangeDetectionStrategy,
    Component,
    contentChild,
    inject,
    input,
    NgZone,
    OnDestroy,
    signal
} from '@angular/core';
import { RightResizableContentDirective } from './right-resizable-content.directive';
import { NgClass } from '@angular/common';

@Component({
    selector: 'app-resizable-splitted-layout',
    standalone: true,
    imports: [NgClass],
    templateUrl: './resizable-splitted-layout.component.html',
    styleUrl: './resizable-splitted-layout.component.scss',
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class ResizableSplittedLayoutComponent implements AfterViewInit, OnDestroy {
    private ngZone = inject(NgZone);

    showRightSide = input<boolean>(true);
    initialLeftWidth = input<number>(30);
    uniqId = input.required<string>();

    rightResizableContent = contentChild(RightResizableContentDirective);

    readonly MIN_WIDTH_PERCENT = 30;
    readonly MAX_WIDTH_PERCENT = 100 - this.MIN_WIDTH_PERCENT;

    leftWidth = signal(this.initialLeftWidth());
    isResizing = signal(false);

    private mouseMoveListener = (e: MouseEvent) => this.onMouseMove(e);
    private mouseUpListener = () => this.stopResize();

    ngAfterViewInit() {
        const storedWidth = localStorage.getItem(this.getStorageKey());
        if (storedWidth) {
            const parsed = parseFloat(storedWidth);
            if (!isNaN(parsed)) {
                this.leftWidth.set(parsed);
            }
        }

        this.ngZone.runOutsideAngular(() => {
            document.addEventListener('mousemove', this.mouseMoveListener);
            document.addEventListener('mouseup', this.mouseUpListener);
        });
    }

    startResize() {
        this.isResizing.set(true);
    }

    private onMouseMove(event: MouseEvent) {
        if (!this.isResizing()) return;

        const container = document.getElementById('container');
        if (!container) return;

        const offsetLeft = container.getBoundingClientRect().left;
        const newWidth = ((event.clientX - offsetLeft) / container.offsetWidth) * 100;

        if (newWidth > this.MIN_WIDTH_PERCENT && newWidth < this.MAX_WIDTH_PERCENT) {
            requestAnimationFrame(() => {
                this.leftWidth.set(newWidth);
                localStorage.setItem(this.getStorageKey(), newWidth.toFixed(2));
            });
        }
    }

    private stopResize() {
        this.isResizing.set(false);
    }

    private getStorageKey(): string {
        return `ResizableSplittedLayoutComponent-leftWidth-${this.uniqId()}`;
    }

    ngOnDestroy() {
        document.removeEventListener('mousemove', this.mouseMoveListener);
        document.removeEventListener('mouseup', this.mouseUpListener);
    }
}
