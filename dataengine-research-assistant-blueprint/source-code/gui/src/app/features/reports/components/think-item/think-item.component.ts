import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { MarkdownViewerComponent } from '../../../shared/components/markdown-viewer/markdown-viewer.component';
import { StringToFlowPipe } from '../../../shared/pipes/string-to-flow.pipe';
import { AsyncPipe } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { style, transition, trigger, animate, state } from '@angular/animations';

@Component({
  selector: 'app-think-item',
  standalone: true,
    imports: [
        MarkdownViewerComponent,
        StringToFlowPipe,
        AsyncPipe
    ],
  templateUrl: './think-item.component.html',
  styleUrl: './think-item.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
    animations: [
        trigger('expandAnimation', [
            state('off', style({ width: '*', opacity: 1 })), // без анимации

            transition('void => on', [
                style({ width: '0px', opacity: 0 }),
                animate('300ms ease-out', style({ width: '*', opacity: 1 }))
            ]),

            transition('on => void', [
                animate('300ms ease-in', style({ width: '0px', opacity: 0 }))
            ]),

            // Без анимации при 'off'
            transition('void => off', [
                style({ width: '*', opacity: 1 }) // сразу отображаем
            ]),
            transition('off => void', [
                style({ width: '0px', opacity: 0 }) // сразу скрываем
            ]),
        ])
    ]
})
export class ThinkItemComponent {
    item = input<any>({})
    index = input(1)
    animateI = input(true)
    showIcon = input(true)
}
