import { AfterViewInit, Directive, DoCheck, ElementRef, input, NgZone, AfterViewChecked } from '@angular/core';
import { AnimationCrontrolService } from '../services/animation-crontrol.service';

@Directive({
    selector: '[appAutoScroll]',
    standalone: true,
})
export class AutoScrollDirective implements AfterViewInit, DoCheck, AfterViewChecked {
    private isUserAtBottom = true;
    private lastScrollHeight = 0;

    disable = input(false);

    constructor(private el: ElementRef, private zone: NgZone, private animation: AnimationCrontrolService) {}

    ngAfterViewInit(): void {
        this.el.nativeElement.addEventListener('scroll', () => this.onScroll());
        this.scrollToBottom();
    }

    ngDoCheck() {
    }

    ngAfterViewChecked(): void {
        const scrollHeight = this.el.nativeElement.scrollHeight;
        if (this.isUserAtBottom && scrollHeight !== this.lastScrollHeight) {
            this.scrollToBottom();
        }
        this.lastScrollHeight = scrollHeight;
    }

    private onScroll(): void {
        const el = this.el.nativeElement;
        const threshold = 10;
        const position = el.scrollTop + el.clientHeight;
        this.isUserAtBottom = position >= el.scrollHeight - threshold;
    }

    private scrollToBottom(): void {
        this.zone.runOutsideAngular(() => {
            setTimeout(() => {
                this.el.nativeElement.scrollTo({
                    top: this.el.nativeElement.scrollHeight,
                    behavior: 'smooth'
                });
            }, 100);
        });
    }
}
