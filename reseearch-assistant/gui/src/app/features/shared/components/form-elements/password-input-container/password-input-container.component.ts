import { Component, ContentChild, ElementRef, ViewChild } from '@angular/core';
import { AppSvgIconComponent } from '../../../../../../../../../orion/management/insightGUI/src/app/shared/components/app-svg-icon/app-svg-icon.component';

@Component({
  selector: 'password-input-container',
  imports: [
    AppSvgIconComponent,
  ],
  standalone: true,
  templateUrl: './password-input-container.component.html',
  styleUrl: './password-input-container.component.scss'
})
export class PasswordInputContainerComponent {
  @ContentChild('input') inputElement!: ElementRef;
  protected isPasswordVisible = false;

  protected onToggle() {
    if (!this.inputElement) return;
    this.isPasswordVisible = !this.isPasswordVisible;
    this.inputElement.nativeElement.type = this.isPasswordVisible ? 'text' : 'password';
  }
}
