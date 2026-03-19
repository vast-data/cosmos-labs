export interface LoginRequest {
  username: string;
  secret_key: string;  // S3 secret key for local users (VMS and tenant from backend config)
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  username: string;
}

export interface UserInfo {
  username: string;
  email?: string;
  auth_type: string;
}

export interface LoginState {
  status: 'pending' | 'success' | 'loading' | 'error';
  error: string | null;
  token: string | null;
  user: string | null;
}

