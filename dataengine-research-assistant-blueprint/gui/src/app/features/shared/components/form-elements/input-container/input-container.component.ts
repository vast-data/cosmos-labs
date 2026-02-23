import { Component, Input } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { NgClass } from '@angular/common';

@Component({
    selector: 'input-container',
    standalone: true,
    templateUrl: './input-container.component.html',
    imports: [
        ReactiveFormsModule,
        NgClass,
    ],
    styleUrl: './input-container.component.scss',
})
export class InputContainerComponent {
    @Input() label = '';
    @Input() for = '';
    @Input() isNarrow = false;
}
