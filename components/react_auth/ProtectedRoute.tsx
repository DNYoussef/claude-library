/**
 * Protected Route Component
 * @module react-auth/ProtectedRoute
 */
import React from 'react';
import { useAuth } from './useAuth';
import type { ProtectedRouteProps } from './types';

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

export default ProtectedRoute;
