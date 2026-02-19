import {
    animate,
    query,
    style,
    transition,
    trigger,
} from '@angular/animations';

export const routeTransition = trigger('routeTransition', [
    transition('* => *', [
        query(':enter', [style({ opacity: 0, position: 'absolute' })], { optional: true }),
        query(':leave', [style({ position: 'absolute' })], { optional: true }),
        query(':leave', [animate('0.2s', style({ opacity: 0 }))], {
            optional: true,
        }),
        query(':enter', [animate('0.2s', style({ opacity: 1, position: 'absolute' }))], {
            optional: true,
        }),
    ]),
]);
