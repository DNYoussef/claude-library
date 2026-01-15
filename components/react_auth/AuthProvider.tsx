/**
 * Auth Provider Component
 * @module react-auth/AuthProvider
 */
import React, { useReducer, useCallback, useEffect, useMemo } from 'react';
import { AuthContext } from './AuthContext';
import type {
  AuthState,
  AuthAction,
  AuthProviderProps,
  AuthContextValue,
  User,
  AuthTokens,
  LoginCredentials,
} from './types';

// Initial state
const initialState: AuthState = {
  isAuthenticated: false,
  isLoading: true,
  user: null,
  tokens: null,
  error: null,
};

// Reducer
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
      return { ...initialState, isLoading: false };
    case 'REFRESH_SUCCESS':
      return { ...state, tokens: action.tokens };
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

// Storage helpers
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

// Provider component
export function AuthProvider({ children, config = {} }: AuthProviderProps): JSX.Element {
  const {
    storage: storageType = 'localStorage',
    storageKey = 'auth',
    refreshThreshold = 300,
    autoRefresh = true,
    onLogin,
    onLogout,
    onRefresh,
  } = config;

  const [state, dispatch] = useReducer(authReducer, initialState);
  const storage = useMemo(() => getStorage(storageType), [storageType]);

  // Load from storage on mount
  useEffect(() => {
    const stored = loadFromStorage(storage, storageKey);
    if (stored && stored.tokens) {
      const now = Date.now() / 1000;
      if (stored.tokens.expiresAt && stored.tokens.expiresAt < now) {
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

  // Auto-refresh
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
  }, [autoRefresh, state.tokens, state.user, refreshThreshold, onRefresh, storage, storageKey]);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      dispatch({ type: 'LOGIN_START' });
      try {
        if (!onLogin) throw new Error('onLogin handler not configured');
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
      if (onLogout) await onLogout();
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
    (role: string) => state.user?.roles?.includes(role) ?? false,
    [state.user]
  );

  const hasPermission = useCallback(
    (permission: string) => state.user?.permissions?.includes(permission) ?? false,
    [state.user]
  );

  const clearError = useCallback(() => dispatch({ type: 'CLEAR_ERROR' }), []);

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

export default AuthProvider;
