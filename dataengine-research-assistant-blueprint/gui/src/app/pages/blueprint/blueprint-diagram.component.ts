import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIcon } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-blueprint-diagram',
  standalone: true,
  imports: [CommonModule, MatIcon, RouterLink],
  templateUrl: './blueprint-diagram.component.html',
  styleUrl: './blueprint-diagram.component.scss',
})
export class BlueprintDiagramComponent {}

