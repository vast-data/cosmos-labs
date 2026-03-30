import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AnimationCrontrolService {

    public animationFinished: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
}
