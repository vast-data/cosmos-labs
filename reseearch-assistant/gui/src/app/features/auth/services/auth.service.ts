import { computed, effect, inject, Injectable, signal } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { SETTINGS } from '../../shared/settings';
import { Router } from '@angular/router';
import { map, of, Observable, catchError } from 'rxjs';

export interface JwtPayload {
    token_type?: string;
    exp?: number;
    iat?: number;
    jti?: string;
    user_id?: number;
    user_type?: string;
    last_login?: string;
    failed_logins?: number;
    tenant_guid?: string | null;
    provider_info?: object | null;
    // Azure AD fields
    sub?: string;
    oid?: string;
    name?: string;
    preferred_username?: string;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
    jwt_token: string;
    jwt_payload: JwtPayload;
}

export interface LoginState {
    status: 'pending' | 'success' | 'loading' | 'error',
    error: string | null,
    token: string | null,
    user: string | null,
    user_id: number | null,
    user_type: string | null,
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    httClient = inject(HttpClient);
    router = inject(Router);

    state = signal<LoginState>({
        status: localStorage.getItem(SETTINGS.LS_KEY_TOKEN) ? 'success' : 'pending',
        error: null,
        token: localStorage.getItem(SETTINGS.LS_KEY_TOKEN),
        user: localStorage.getItem(SETTINGS.USER_KEY_TOKEN),
        user_id: null,
        user_type: null,
    });

    status = computed(() => this.state().status);
    token = computed(() => this.state().token);
    user = computed(() => this.state().user);
    user_id = computed(() => this.state().user_id);
    user_type = computed(() => this.state().user_type);
    error = computed(() => this.state().error);

    constructor() {
        effect(() => {
            const tokenValue = this.token();
            if (tokenValue) {
                localStorage.setItem(SETTINGS.LS_KEY_TOKEN, tokenValue);
            } else {
                localStorage.removeItem(SETTINGS.LS_KEY_TOKEN);
            }
        });
        effect(() => {
            const userValue = this.user();
            if (userValue) {
                localStorage.setItem(SETTINGS.USER_KEY_TOKEN, userValue);
            } else {
                localStorage.removeItem(SETTINGS.USER_KEY_TOKEN);
            }
        });
    }

    login(username: string, password: string, forceData?: any) {
        this.state.update((state) => ({ ...state, status: 'loading', error: null }));

        if (SETTINGS.MOCK_MODE) {
            // Minimal mock: immediately set token and user, navigate to default URL
            const mockToken = 'mock_token';
            const mockUser = username || 'demo';
            this.state.update((state) => ({
                ...state,
                token: mockToken,
                user: mockUser,
                status: 'success'
            }));
            this.router.navigate([SETTINGS.DEFAULT_URL]);
            return;
        }

        const headers = new HttpHeaders({
            'Content-Type': 'application/json'
        });
        const data = { username, password } as { username?: string; password?: string };

        this.httClient.post<LoginResponse>('/api/v1/login', forceData ? forceData : data, { headers }).subscribe(
            {
                next: (response) => {
                    // Handle both local user (user_id) and Azure AD (sub/oid) JWT payloads
                    const userId = response.jwt_payload?.user_id ?? response.jwt_payload?.sub ?? response.jwt_payload?.oid ?? null;
                    const userType = response.jwt_payload?.user_type ?? 'USER';
                    
                    this.state.update((state) => ({
                        ...state,
                        token: response.access_token,
                        user: userId?.toString() ?? null,
                        user_id: typeof userId === 'number' ? userId : null,
                        user_type: userType,
                        status: 'success'
                    }));
                    console.log(this.state());
                    
                    // Trigger data loading after login - services will be instantiated when AppLayoutComponent loads
                    // Use setTimeout to ensure navigation happens first and services are available
                    setTimeout(() => {
                        // Services will auto-load via effect(), but we can also trigger explicitly if needed
                        console.log('Login complete, data should load automatically via services');
                    }, 100);
                    
                    this.router.navigate([SETTINGS.DEFAULT_URL]);
                },
                error: (response) => {
                    console.log(response);
                    this.state.update((state) => ({
                        ...state,
                        token: null,
                        user: null,
                        user_id: null,
                        user_type: null,
                        status: 'error',
                        error: response.error?.detail || 'Authentication failed'
                    }));
                }
            }
        );
    }

    logout() {
        this.state.update((state) => ({
            ...state,
            status: 'pending',
            token: null,
            user: null,
            user_id: null,
            user_type: null
        }));
        this.router.navigate(['/login']);
    }

    exchangeSessionToken(sessionId: string): Observable<void> {
        this.state.update((state) => ({ ...state, status: 'loading', error: null }));
        
        return this.httClient.get<{ token: string }>(`${SETTINGS.BASE_API_URL}/auth/exchange-session?session_id=${sessionId}`)
            .pipe(
                map((response) => {
                    console.log('Session exchange response received');
                    if (response.token) {
                        // Set token immediately and synchronously - this must happen before any other code
                        console.log('Setting token immediately, length:', response.token.length);
                        this.loginWithToken(response.token);
                        
                        // Force a synchronous check - signals update synchronously
                        const tokenAfterSet = this.token();
                        console.log('Token after setting:', tokenAfterSet ? `Set (${tokenAfterSet.length} chars)` : 'NOT SET!');
                        
                        // Verify token is set - if not, something is wrong
                        if (!tokenAfterSet) {
                            console.error('CRITICAL: Token was not set in state after loginWithToken!');
                            // Try setting it directly as a fallback
                            this.state.update((state) => ({ ...state, token: response.token }));
                            const tokenAfterDirectSet = this.token();
                            if (!tokenAfterDirectSet) {
                                throw new Error('Failed to set token in state');
                            }
                        }
                    } else {
                        this.state.update((state) => ({
                            ...state,
                            status: 'error',
                            error: 'No token received from session exchange'
                        }));
                        this.router.navigate(['/login'], { queryParams: { error: 'no_token' } });
                        throw new Error('No token received');
                    }
                }),
                catchError((error) => {
                    console.error('Error exchanging session token:', error);
                    this.state.update((state) => ({
                        ...state,
                        status: 'error',
                        error: error.error?.detail || 'Failed to exchange session token'
                    }));
                    // Redirect to login on error
                    this.router.navigate(['/login'], { queryParams: { error: 'session_exchange_failed' } });
                    throw error;
                })
            );
    }

    loginWithToken(token: string) {
        console.log('loginWithToken called with token length:', token?.length);
        this.state.update((state) => ({ ...state, status: 'loading', error: null }));

        try {
            // Decode JWT to get user info
            const payload = this.decodeJwtPayload(token);
            console.log('Decoded Azure AD token payload:', payload);
            
            // Azure AD tokens use 'sub' or 'oid' for user ID, 'name' or 'preferred_username' for username
            const user_id = payload?.user_id || payload?.sub || payload?.oid || payload?.name || 'unknown';
            const user_type = payload?.user_type || payload?.userType || 'azuread';
            const username = payload?.name || payload?.preferred_username || payload?.email || user_id.toString();

            // Set token immediately and synchronously
            this.state.update((state) => ({
                ...state,
                token: token,
                user: username,
                user_id: typeof user_id === 'number' ? user_id : (user_id !== 'unknown' ? parseInt(user_id) || 0 : 0),
                user_type: user_type,
                status: 'success'
            }));

            // Verify token is set immediately
            const currentToken = this.token();
            console.log('Login state after token update:', {
                token: currentToken ? `${currentToken.substring(0, 20)}...` : 'null',
                tokenLength: currentToken?.length,
                user: this.user(),
                status: this.status()
            });
            
            if (!currentToken) {
                console.error('ERROR: Token was not set in state!');
            }
            
            // Check current route - if already on a valid page, don't navigate
            const currentUrl = this.router.url;
            const isOnValidPage = currentUrl.includes('/chat/') || currentUrl.includes('/sessions') || currentUrl === '/' || currentUrl.startsWith('/#/chat');
            
            // Use setTimeout to ensure state is persisted before navigation
            setTimeout(() => {
                if (!isOnValidPage) {
                    this.router.navigate([SETTINGS.DEFAULT_URL]);
                }
            }, 100);
        } catch (error: any) {
            console.error('Error logging in with token:', error);
            this.state.update((state) => ({
                ...state,
                token: null,
                user: null,
                user_id: null,
                user_type: null,
                status: 'error',
                error: `Failed to process authentication token: ${error.message || error}`
            }));
        }
    }

    private decodeJwtPayload(token: string): any {
        try {
            const parts = token.split('.');
            if (parts.length !== 3) {
                throw new Error('Invalid token format');
            }
            const payload = parts[1];
            const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(
                atob(base64)
                    .split('')
                    .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                    .join('')
            );
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('Error decoding JWT:', error);
            return {};
        }
    }

    verifyToken() {
        const token = this.token();
        if (!token) {
            return of(false);
        }

        return this.httClient.get<{ valid: boolean; username: string }>(`${SETTINGS.BASE_API_URL}/auth/verify`).pipe(
            map((response) => {
                if (response.valid && response.username) {
                    this.state.update((state) => ({ ...state, user: response.username }));
                    return true;
                }
                return false;
            })
        );
    }

}
