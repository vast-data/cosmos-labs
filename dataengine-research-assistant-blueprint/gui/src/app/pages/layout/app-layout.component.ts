import { Component, OnInit, inject, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, ActivatedRoute, Router } from '@angular/router';
import { TopBarComponent } from './top-bar/top-bar.component';
import { SidebarComponent } from './sidebar/sidebar.component';
import { AuthService } from '../../features/auth/services/auth.service';
import { SessionsService } from '../../features/sessions/services/sessions.service';
import { CollectionsService } from '../../features/collections/services/collections.service';

@Component({
  selector: 'app-app-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    TopBarComponent,
    SidebarComponent,
  ],
  templateUrl: './app-layout.component.html',
  styleUrl: './app-layout.component.scss',
})
export class AppLayoutComponent implements OnInit {
  route = inject(ActivatedRoute);
  router = inject(Router);
  authService = inject(AuthService);
  sessionsService = inject(SessionsService);
  collectionsService = inject(CollectionsService);

  constructor() {
    // Watch for auth status changes to load data when login completes
    // This effect runs immediately when component is instantiated
    effect(() => {
      const token = this.authService.token();
      const status = this.authService.status();
      
      console.log('AppLayoutComponent effect: token =', token ? 'present' : 'missing', ', status =', status);
      
      if (token && status === 'success') {
        console.log('AppLayoutComponent: Auth status is success, loading data');
        // Use setTimeout to ensure this runs after navigation completes
        setTimeout(() => {
          console.log('AppLayoutComponent: Explicitly calling loadSessions and loadCollections');
          this.sessionsService.loadSessions();
          this.collectionsService.loadCollections();
        }, 100);
      }
    });
  }

  ngOnInit() {
    // Ensure services are instantiated and load data if token is available
    const token = this.authService.token();
    const status = this.authService.status();
    console.log('AppLayoutComponent ngOnInit: token =', token ? 'present' : 'missing', ', status =', status);
    
    if (token && status === 'success') {
      console.log('AppLayoutComponent: Token available on init, triggering data load immediately');
      this.sessionsService.loadSessions();
      this.collectionsService.loadCollections();
    }

    // Check for Azure AD session_id in query params (from redirect)
    this.route.queryParams.subscribe(params => {
      const sessionId = params['session_id'];
      const provider = params['provider'];
      
      if (sessionId && provider === 'azuread') {
        // Exchange session_id for token
        // loginWithToken will handle navigation, so we just need to clean URL after a delay
        this.authService.exchangeSessionToken(sessionId).subscribe({
          next: () => {
            // Token exchange successful, load data immediately
            console.log('AppLayoutComponent: Token exchange successful, loading data');
            setTimeout(() => {
              this.sessionsService.loadSessions();
              this.collectionsService.loadCollections();
            }, 100);
            
            // Wait a bit then clean URL
            setTimeout(() => {
              this.router.navigate([], { 
                relativeTo: this.route,
                queryParams: {},
                replaceUrl: true
              });
            }, 200);
          },
          error: (err) => {
            console.error('Error in AppLayoutComponent session exchange:', err);
            // On error, redirect to login
            this.router.navigate(['/login'], { queryParams: { error: 'session_exchange_failed' } });
          }
        });
      }
    });
  }
}