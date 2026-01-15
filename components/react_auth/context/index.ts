/**
 * React Auth Context Component
 *
 * Type-safe authentication context with hooks for React applications.
 *
 * References:
 * - https://github.com/authts/react-oidc-context
 * - https://github.com/bezkoder/react-typescript-authentication-example
 *
 * Example:
 *   import { AuthProvider, useAuth } from 'library/react-auth/context';
 *
 *   function App() {
 *     return (
 *       <AuthProvider config={{ onLogin, onLogout }}>
 *         <MyApp />
 *       </AuthProvider>
 *     );
 *   }
 */

export {
  // Provider
  AuthProvider,
  // Hooks
  useAuth,
  useUser,
  useIsAuthenticated,
  useHasRole,
  useHasPermission,
  // Components
  ProtectedRoute,
  // Types
  type User,
  type AuthTokens,
  type AuthState,
  type AuthConfig,
  type AuthContextValue,
  type LoginCredentials,
  type AuthProviderProps,
  type ProtectedRouteProps,
} from './AuthContext';
