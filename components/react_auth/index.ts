/**
 * React Auth Library
 *
 * Type-safe authentication context with hooks for React applications.
 * Supports JWT, OAuth, and session-based authentication.
 *
 * @module react-auth
 * @version 1.0.0
 *
 * Based on:
 * - react-oidc-context: https://github.com/authts/react-oidc-context
 * - bezkoder patterns: https://github.com/bezkoder/react-typescript-authentication-example
 *
 * @example
 * import { AuthProvider, useAuth, ProtectedRoute } from '@library/react-auth';
 *
 * function App() {
 *   return (
 *     <AuthProvider config={{ onLogin, onLogout }}>
 *       <ProtectedRoute unauthenticatedFallback={<Login />}>
 *         <Dashboard />
 *       </ProtectedRoute>
 *     </AuthProvider>
 *   );
 * }
 */

// Context
export { AuthContext } from './AuthContext';

// Provider
export { AuthProvider } from './AuthProvider';

// Hooks
export {
  useAuth,
  useUser,
  useIsAuthenticated,
  useHasRole,
  useHasPermission,
} from './useAuth';

// Components
export { ProtectedRoute } from './ProtectedRoute';

// Types
export type {
  User,
  AuthTokens,
  AuthState,
  LoginCredentials,
  AuthConfig,
  AuthContextValue,
  AuthProviderProps,
  ProtectedRouteProps,
  AuthAction,
} from './types';

// Re-export from context folder for backward compatibility
export * from './context';
