/**
 * React Auth Context Component
 *
 * Type-safe authentication context with hooks for React applications.
 * Supports JWT, OAuth, and session-based authentication.
 *
 * Based on:
 * - react-oidc-context: https://github.com/authts/react-oidc-context
 * - bezkoder patterns: https://github.com/bezkoder/react-typescript-authentication-example
 *
 * Features:
 * - Type-safe auth state and actions
 * - Token refresh handling
 * - Protected route support
 * - Persistence (localStorage/sessionStorage)
 * - Loading and error states
 *
 * Example:
 *   import { AuthProvider, useAuth } from 'library/react-auth/context';
 *
 *   function App() {
 *     return (
 *       <AuthProvider>
 *         <MyApp />
 *       </AuthProvider>
 *     );
 *   }
 *
 *   function LoginButton() {
 *     const { login, isAuthenticated, user } = useAuth();
 *     if (isAuthenticated) return <span>Hello, {user?.name}</span>;
 *     return <button onClick={() => login(creds)}>Login</button>;
 *   }
 */

import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  useMemo,
  type ReactNode,
} from 'react';

// =============================================================================
// TYPES
// =============================================================================

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
  expiresAt?: number; // Unix timestamp
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
  /** Storage type for persistence */
  storage?: 'localStorage' | 'sessionStorage' | 'none';
  /** Storage key prefix */
  storageKey?: string;
  /** Token refresh threshold in seconds */
  refreshThreshold?: number;
  /** Auto-refresh tokens */
  autoRefresh?: boolean;
  /** Login handler */
  onLogin?: (credentials: LoginCredentials) => Promise<{ user: User; tokens: AuthTokens }>;
  /** Logout handler */
  onLogout?: () => Promise<void>;
  /** Token refresh handler */
  onRefresh?: (refreshToken: string) => Promise<AuthTokens>;
  /** Get current user from token */
  onGetUser?: (accessToken: string) => Promise<User>;
}

export interface AuthContextValue extends AuthState {
  /** Login with credentials */
  login: (credentials: LoginCredentials) => Promise<void>;
  /** Logout and clear state */
  logout: () => Promise<void>;
  /** Manually refresh tokens */
  refreshTokens: () => Promise<void>;
  /** Check if user has role */
  hasRole: (role: string) => boolean;
  /** Check if user has permission */
  hasPermission: (permission: string) => boolean;
  /** Clear error state */
  clearError: () => void;
}

// =============================================================================
// REDUCER
// =============================================================================

type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; user: User; tokens: AuthTokens }
  | { type: 'LOGIN_ERROR'; error: string }
  | { type: 'LOGOUT' }
  | { type: 'REFRESH_SUCCESS'; tokens: AuthTokens }
  | { type: 'SET_USER'; user: User }
  | { type: 'SET_LOADING'; isLoading: boolean }
  | { type: 'CLEAR_ERROR' };

const initialState: AuthState = {
  isAuthenticated: false,
  isLoading: true,
  user: null,
  tokens: null,
  error: null,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, isLoading: true, error: null };

    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        isLoading: false,
        user: action.user,
        tokens: action.tokens,
        error: null,
      };

    case 'LOGIN_ERROR':
      return {
        ...state,
        isAuthenticated: false,
        isLoading: false,
        user: null,
        tokens: null,
        error: action.error,
      };

    case 'LOGOUT':
      return {
        ...initialState,
        isLoading: false,
      };

    case 'REFRESH_SUCCESS':
      return {
        ...state,
        tokens: action.tokens,
      };

    case 'SET_USER':
      return { ...state, user: action.user };

    case 'SET_LOADING':
      return { ...state, isLoading: action.isLoading };

    case 'CLEAR_ERROR':
      return { ...state, error: null };

    default:
      return state;
  }
}

// =============================================================================
// CONTEXT
// =============================================================================

const AuthContext = createContext<AuthContextValue | null>(null);

// =============================================================================
// STORAGE HELPERS
// =============================================================================

function getStorage(type: 'localStorage' | 'sessionStorage' | 'none'): Storage | null {
  if (type === 'none' || typeof window === 'undefined') return null;
  return type === 'localStorage' ? window.localStorage : window.sessionStorage;
}

function loadFromStorage(
  storage: Storage | null,
  key: string
): { user: User; tokens: AuthTokens } | null {
  if (!storage) return null;
  try {
    const data = storage.getItem(key);
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

function saveToStorage(
  storage: Storage | null,
  key: string,
  data: { user: User; tokens: AuthTokens }
): void {
  if (!storage) return;
  try {
    storage.setItem(key, JSON.stringify(data));
  } catch {
    // Storage full or unavailable
  }
}

function clearStorage(storage: Storage | null, key: string): void {
  if (!storage) return;
  try {
    storage.removeItem(key);
  } catch {
    // Ignore
  }
}

// =============================================================================
// PROVIDER
// =============================================================================

export interface AuthProviderProps {
  children: ReactNode;
  config?: AuthConfig;
}

export function AuthProvider({ children, config = {} }: AuthProviderProps): JSX.Element {
  const {
    storage: storageType = 'localStorage',
    storageKey = 'auth',
    refreshThreshold = 300, // 5 minutes
    autoRefresh = true,
    onLogin,
    onLogout,
    onRefresh,
    onGetUser,
  } = config;

  const [state, dispatch] = useReducer(authReducer, initialState);
  const storage = useMemo(() => getStorage(storageType), [storageType]);

  // Load auth state from storage on mount
  useEffect(() => {
    const stored = loadFromStorage(storage, storageKey);
    if (stored && stored.tokens) {
      // Check if token is expired
      const now = Date.now() / 1000;
      if (stored.tokens.expiresAt && stored.tokens.expiresAt < now) {
        // Token expired, try refresh or logout
        if (stored.tokens.refreshToken && onRefresh) {
          onRefresh(stored.tokens.refreshToken)
            .then((tokens) => {
              dispatch({ type: 'LOGIN_SUCCESS', user: stored.user, tokens });
              saveToStorage(storage, storageKey, { user: stored.user, tokens });
            })
            .catch(() => {
              dispatch({ type: 'LOGOUT' });
              clearStorage(storage, storageKey);
            });
        } else {
          dispatch({ type: 'LOGOUT' });
          clearStorage(storage, storageKey);
        }
      } else {
        dispatch({ type: 'LOGIN_SUCCESS', user: stored.user, tokens: stored.tokens });
      }
    } else {
      dispatch({ type: 'SET_LOADING', isLoading: false });
    }
  }, [storage, storageKey, onRefresh]);

  // Auto-refresh tokens
  useEffect(() => {
    if (!autoRefresh || !state.tokens?.expiresAt || !state.tokens?.refreshToken || !onRefresh) {
      return;
    }

    const now = Date.now() / 1000;
    const expiresIn = state.tokens.expiresAt - now;
    const refreshIn = Math.max(0, (expiresIn - refreshThreshold) * 1000);

    const timer = setTimeout(async () => {
      try {
        const tokens = await onRefresh(state.tokens!.refreshToken!);
        dispatch({ type: 'REFRESH_SUCCESS', tokens });
        if (state.user) {
          saveToStorage(storage, storageKey, { user: state.user, tokens });
        }
      } catch {
        dispatch({ type: 'LOGOUT' });
        clearStorage(storage, storageKey);
      }
    }, refreshIn);

    return () => clearTimeout(timer);
  }, [
    autoRefresh,
    state.tokens,
    state.user,
    refreshThreshold,
    onRefresh,
    storage,
    storageKey,
  ]);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      dispatch({ type: 'LOGIN_START' });
      try {
        if (!onLogin) {
          throw new Error('onLogin handler not configured');
        }
        const { user, tokens } = await onLogin(credentials);
        dispatch({ type: 'LOGIN_SUCCESS', user, tokens });
        saveToStorage(storage, storageKey, { user, tokens });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Login failed';
        dispatch({ type: 'LOGIN_ERROR', error: message });
        throw err;
      }
    },
    [onLogin, storage, storageKey]
  );

  const logout = useCallback(async () => {
    try {
      if (onLogout) {
        await onLogout();
      }
    } finally {
      dispatch({ type: 'LOGOUT' });
      clearStorage(storage, storageKey);
    }
  }, [onLogout, storage, storageKey]);

  const refreshTokens = useCallback(async () => {
    if (!state.tokens?.refreshToken || !onRefresh) {
      throw new Error('Cannot refresh: no refresh token or handler');
    }
    const tokens = await onRefresh(state.tokens.refreshToken);
    dispatch({ type: 'REFRESH_SUCCESS', tokens });
    if (state.user) {
      saveToStorage(storage, storageKey, { user: state.user, tokens });
    }
  }, [state.tokens, state.user, onRefresh, storage, storageKey]);

  const hasRole = useCallback(
    (role: string) => {
      return state.user?.roles?.includes(role) ?? false;
    },
    [state.user]
  );

  const hasPermission = useCallback(
    (permission: string) => {
      return state.user?.permissions?.includes(permission) ?? false;
    },
    [state.user]
  );

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      logout,
      refreshTokens,
      hasRole,
      hasPermission,
      clearError,
    }),
    [state, login, logout, refreshTokens, hasRole, hasPermission, clearError]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// =============================================================================
// HOOKS
// =============================================================================

/**
 * Access auth context.
 * Must be used within AuthProvider.
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Get current user or null.
 */
export function useUser(): User | null {
  const { user } = useAuth();
  return user;
}

/**
 * Get authentication status.
 */
export function useIsAuthenticated(): boolean {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}

/**
 * Check if user has specific role.
 */
export function useHasRole(role: string): boolean {
  const { hasRole } = useAuth();
  return hasRole(role);
}

/**
 * Check if user has specific permission.
 */
export function useHasPermission(permission: string): boolean {
  const { hasPermission } = useAuth();
  return hasPermission(permission);
}

// =============================================================================
// PROTECTED ROUTE COMPONENT
// =============================================================================

export interface ProtectedRouteProps {
  children: ReactNode;
  /** Required role (optional) */
  requiredRole?: string;
  /** Required permission (optional) */
  requiredPermission?: string;
  /** Fallback when loading */
  loadingFallback?: ReactNode;
  /** Fallback when not authenticated */
  unauthenticatedFallback?: ReactNode;
  /** Fallback when not authorized */
  unauthorizedFallback?: ReactNode;
}

export function ProtectedRoute({
  children,
  requiredRole,
  requiredPermission,
  loadingFallback = null,
  unauthenticatedFallback = null,
  unauthorizedFallback = null,
}: ProtectedRouteProps): JSX.Element | null {
  const { isAuthenticated, isLoading, hasRole, hasPermission } = useAuth();

  if (isLoading) {
    return <>{loadingFallback}</>;
  }

  if (!isAuthenticated) {
    return <>{unauthenticatedFallback}</>;
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return <>{unauthorizedFallback}</>;
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <>{unauthorizedFallback}</>;
  }

  return <>{children}</>;
}
