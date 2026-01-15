/**
 * React Auth Types
 * @module react-auth/types
 */
import type { ReactNode } from 'react';

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  roles?: string[];
  permissions?: string[];
  metadata?: Record<string, unknown>;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: number;
  tokenType?: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  tokens: AuthTokens | null;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthConfig {
  storage?: 'localStorage' | 'sessionStorage' | 'none';
  storageKey?: string;
  refreshThreshold?: number;
  autoRefresh?: boolean;
  onLogin?: (credentials: LoginCredentials) => Promise<{ user: User; tokens: AuthTokens }>;
  onLogout?: () => Promise<void>;
  onRefresh?: (refreshToken: string) => Promise<AuthTokens>;
  onGetUser?: (accessToken: string) => Promise<User>;
}

export interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<void>;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
  clearError: () => void;
}

export interface AuthProviderProps {
  children: ReactNode;
  config?: AuthConfig;
}

export interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
  loadingFallback?: ReactNode;
  unauthenticatedFallback?: ReactNode;
  unauthorizedFallback?: ReactNode;
}

export type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; user: User; tokens: AuthTokens }
  | { type: 'LOGIN_ERROR'; error: string }
  | { type: 'LOGOUT' }
  | { type: 'REFRESH_SUCCESS'; tokens: AuthTokens }
  | { type: 'SET_USER'; user: User }
  | { type: 'SET_LOADING'; isLoading: boolean }
  | { type: 'CLEAR_ERROR' };
