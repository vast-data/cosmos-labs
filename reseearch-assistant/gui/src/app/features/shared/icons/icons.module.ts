import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { MatIconRegistry } from '@angular/material/icon';
import { DomSanitizer } from '@angular/platform-browser';
import { SVGICONS } from './icons.config';

@NgModule({
    declarations: [],
    imports: [CommonModule, HttpClientModule],
})
export class IconsModule {
    constructor(
        private matIconRegistry: MatIconRegistry,
        private sanitizer: DomSanitizer,
    ) {
        for (const name of SVGICONS) {
            this.matIconRegistry.addSvgIcon(
                name,
                this.sanitizer.bypassSecurityTrustResourceUrl(`/assets/icons/${name}.svg`));
        }
    }

}
