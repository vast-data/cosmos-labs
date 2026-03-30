import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { Document } from '../../../shared/models/sources.model';

@Component({
  selector: 'app-source-card',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule, MatMenuModule],
  templateUrl: './source-card.component.html',
  styleUrls: ['./source-card.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SourceCardComponent {
  source = input.required<Document>();
  collectionName = input.required<string>();
  className = input<string>('');
  edit = output<Document>();
  delete = output<Document>();

  // Placeholder tags (same as React version)
  placeholderTags = ['tag', 'Feature', 'Bug', 'Enhancement'];

  onEdit() {
    this.edit.emit(this.source());
  }

  onDelete() {
    if (confirm(`Are you sure you want to delete "${this.source().document_name}"?`)) {
      this.delete.emit(this.source());
    }
  }

  get displayTags(): string[] {
    return this.source().tags && this.source().tags.length > 0
      ? this.source().tags
      : this.placeholderTags;
  }
}
