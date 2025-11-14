export interface LoginRequest {
  username: string;
  password: string;
  vast_host: string;
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

