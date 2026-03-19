import { Component, inject, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeService } from './shared/services/theme.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  // Initialize theme service early to apply theme before any components render
  private themeService = inject(ThemeService);

  ngOnInit() {
    // Theme service initializes automatically via constructor
    // This injection ensures it's created early in the app lifecycle
  }
}

