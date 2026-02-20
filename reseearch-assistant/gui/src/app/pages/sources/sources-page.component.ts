import { ChangeDetectionStrategy, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CollectionSourcesComponent } from '../../features/sources/components/collection-sources/collection-sources.component';

@Component({
  selector: 'app-sources-page',
  standalone: true,
  imports: [CommonModule, CollectionSourcesComponent],
  templateUrl: './sources-page.component.html',
  styleUrls: ['./sources-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SourcesPageComponent {}

