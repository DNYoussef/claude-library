/**
 * React Auth Hooks
 * @module react-auth/useAuth
 */
import { useContext } from 'react';
import { AuthContext } from './AuthContext';
import type { AuthContextValue, User } from './types';

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function useUser(): User | null {
  const { user } = useAuth();
  return user;
}

export function useIsAuthenticated(): boolean {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}

export function useHasRole(role: string): boolean {
  const { hasRole } = useAuth();
  return hasRole(role);
}

export function useHasPermission(permission: string): boolean {
  const { hasPermission } = useAuth();
  return hasPermission(permission);
}
