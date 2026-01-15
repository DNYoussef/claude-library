# React Auth Library

Type-safe authentication context with hooks for React applications. Supports JWT, OAuth, and session-based authentication.

## Installation

```bash
npm install react
# TypeScript users: types included
```

## Features

- **Type-Safe**: Full TypeScript support with strict typing
- **SSR-Compatible**: Works with Next.js, Remix, and other SSR frameworks
- **Token Refresh**: Automatic token refresh with configurable threshold
- **Persistence**: localStorage/sessionStorage support
- **Protected Routes**: Route guard with role/permission checks
- **Hooks**: Convenient hooks for auth state access

## Quick Start

```tsx
import { AuthProvider, useAuth, ProtectedRoute } from '@library/react-auth';

// 1. Configure handlers
const authConfig = {
  onLogin: async (credentials) => {
    const res = await api.post('/auth/login', credentials);
    return { user: res.user, tokens: res.tokens };
  },
  onLogout: async () => {
    await api.post('/auth/logout');
  },
  onRefresh: async (refreshToken) => {
    const res = await api.post('/auth/refresh', { refreshToken });
    return res.tokens;
  },
};

// 2. Wrap your app
function App() {
  return (
    <AuthProvider config={authConfig}>
      <Router />
    </AuthProvider>
  );
}

// 3. Use auth in components
function LoginPage() {
  const { login, isLoading, error } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    await login({ email, password });
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error}</div>}
      <button disabled={isLoading}>Login</button>
    </form>
  );
}

// 4. Protect routes
function Routes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute
            loadingFallback={<Spinner />}
            unauthenticatedFallback={<Navigate to="/login" />}
          >
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute
            requiredRole="admin"
            unauthorizedFallback={<AccessDenied />}
          >
            <AdminPanel />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
```

## API Reference

### AuthProvider

```tsx
<AuthProvider config={authConfig}>
  {children}
</AuthProvider>
```

**Config Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| storage | 'localStorage' \| 'sessionStorage' \| 'none' | 'localStorage' | Storage type |
| storageKey | string | 'auth' | Storage key |
| refreshThreshold | number | 300 | Seconds before expiry to refresh |
| autoRefresh | boolean | true | Auto-refresh tokens |
| onLogin | function | - | Login handler |
| onLogout | function | - | Logout handler |
| onRefresh | function | - | Token refresh handler |

### useAuth Hook

```tsx
const {
  // State
  isAuthenticated,
  isLoading,
  user,
  tokens,
  error,
  // Actions
  login,
  logout,
  refreshTokens,
  hasRole,
  hasPermission,
  clearError,
} = useAuth();
```

### Specialized Hooks

```tsx
const user = useUser();                    // User | null
const isAuth = useIsAuthenticated();       // boolean
const isAdmin = useHasRole('admin');       // boolean
const canEdit = useHasPermission('edit');  // boolean
```

### ProtectedRoute

```tsx
<ProtectedRoute
  requiredRole="admin"           // Optional role check
  requiredPermission="edit"      // Optional permission check
  loadingFallback={<Spinner />}
  unauthenticatedFallback={<Login />}
  unauthorizedFallback={<AccessDenied />}
>
  {children}
</ProtectedRoute>
```

## Types

```tsx
interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  roles?: string[];
  permissions?: string[];
  metadata?: Record<string, unknown>;
}

interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: number;  // Unix timestamp
  tokenType?: string;
}

interface LoginCredentials {
  email: string;
  password: string;
}
```

## File Structure

```
react-auth/
  AuthContext.tsx    # Context definition
  AuthProvider.tsx   # Provider with state management
  useAuth.ts         # Auth hooks
  ProtectedRoute.tsx # Route guard component
  types.ts           # TypeScript definitions
  index.ts           # Public exports
  README.md          # Documentation
  context/           # Legacy exports (backward compat)
```

## Sources

- [react-oidc-context](https://github.com/authts/react-oidc-context)
- [react-typescript-authentication-example](https://github.com/bezkoder/react-typescript-authentication-example)
