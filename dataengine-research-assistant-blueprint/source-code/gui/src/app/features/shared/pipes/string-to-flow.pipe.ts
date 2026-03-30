import { inject, Pipe, PipeTransform } from '@angular/core';
import { concatMap, delay, finalize, from, Observable, of, scan } from 'rxjs';
import { AnimationCrontrolService } from '../services/animation-crontrol.service';

@Pipe({
  name: 'stringToFlow',
  standalone: true
})
export class StringToFlowPipe implements PipeTransform {

    animFinishedService = inject(AnimationCrontrolService)
    transform(input: string, animateFirst500Symbols = false): Observable<string> {
        this.animFinishedService.animationFinished.next(false);
        if (!input) {
            return of('');
        }

        const step = 27;
        const delayMs = 90;

        const chunks: string[]  = [];
        for (let i = 0; i < input.length; i += step) {
            chunks.push(input.slice(i, i + step));
            if (animateFirst500Symbols && chunks.length * 7 > 500) {
                chunks.push(input.slice(i + step, input.length));
                break;
            }
        }

        return from(chunks).pipe(
            concatMap((chunk) => {
                    return of(chunk).pipe(delay(delayMs));
                }
            ),
            scan((acc, char) => acc + char, ''),
            finalize(() => {
                this.animFinishedService.animationFinished.next(true);
            })
        );
    }

}
