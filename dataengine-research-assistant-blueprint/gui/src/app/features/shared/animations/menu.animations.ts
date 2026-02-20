import {
    animate,
    style,
    transition,
    trigger
} from '@angular/animations';

export const showHideAnimation = trigger('showHideAnimation', [
    transition(':enter', [
        style({ width: '0px', overflow: 'hidden' }), // Начальное состояние
        animate('300ms ease-out', style({ width: '*' })) // Конечное состояние (автоматическая ширина)
    ]),
    transition(':leave', [
        animate('300ms ease-in', style({ width: '0px', overflow: 'hidden' })) // Конечное состояние
    ])
]);
