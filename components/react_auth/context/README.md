# React Auth Context Component

Type-safe authentication context with hooks for React applications. Supports JWT, OAuth, and session-based auth.

## Features

- Type-safe auth state and actions
- Token refresh handling with auto-refresh
- Protected route support with role/permission checks
- Persistence (localStorage/sessionStorage)
- Loading and error states
- SSR-safe

## Usage

### Basic Setup

```tsx
import { AuthProvider, useAuth } from 'library/react-auth/context';

// Configure auth handlers
const authConfig = {
  onLogin: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return {
      user: response.data.user,
      tokens: {
        accessToken: response.data.accessToken,
        refreshToken: response.data.refreshToken,
        expiresAt: Date.now() / 1000 + 3600, // 1 hour
      },
    };
  },
  onLogout: async () => {
    await api.post('/auth/logout');
  },
  onRefresh: async (refreshToken) => {
    const response = await api.post('/auth/refresh', { refreshToken });
    return response.data.tokens;
  },
};

function App() {
  return (
    <AuthProvider config={authConfig}>
      <MyApp />
    </AuthProvider>
  );
}
```

### Using Auth Hook

```tsx
import { useAuth } from 'library/react-auth/context';

function LoginButton() {
  const { login, logout, isAuthenticated, user, isLoading, error } = useAuth();

  if (isLoading) return <Spinner />;

  if (isAuthenticated) {
    return (
      <div>
        <span>Hello, {user?.name}</span>
        <button onClick={logout}>Logout</button>
      </div>
    );
  }

  const handleLogin = async () => {
    try {
      await login({ email: 'user@example.com', password: 'secret' });
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  return (
    <div>
      {error && <div className="error">{error}</div>}
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}
```

### Protected Routes

```tsx
import { ProtectedRoute } from 'library/react-auth/context';

function App() {
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

### Role & Permission Checks

```tsx
import { useAuth, useHasRole, useHasPermission } from 'library/react-auth/context';

function AdminFeature() {
  const { hasRole, hasPermission } = useAuth();

  // Or use dedicated hooks
  const isAdmin = useHasRole('admin');
  const canEdit = useHasPermission('posts:edit');

  if (!isAdmin) return null;

  return (
    <div>
      <h2>Admin Panel</h2>
      {canEdit && <EditButton />}
    </div>
  );
}
```

### Specialized Hooks

```tsx
import {
  useUser,
  useIsAuthenticated,
  useHasRole,
  useHasPermission,
} from 'library/react-auth/context';

function UserInfo() {
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const isAdmin = useHasRole('admin');

  if (!isAuthenticated) return <span>Guest</span>;

  return (
    <span>
      {user?.name} {isAdmin && '(Admin)'}
    </span>
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

```typescript
interface AuthConfig {
  storage?: 'localStorage' | 'sessionStorage' | 'none';
  storageKey?: string;       // Default: 'auth'
  refreshThreshold?: number; // Seconds before expiry to refresh (default: 300)
  autoRefresh?: boolean;     // Auto-refresh tokens (default: true)
  onLogin?: (credentials) => Promise<{ user, tokens }>;
  onLogout?: () => Promise<void>;
  onRefresh?: (refreshToken) => Promise<tokens>;
  onGetUser?: (accessToken) => Promise<User>;
}
```

### useAuth Hook

```typescript
const {
  // State
  isAuthenticated: boolean,
  isLoading: boolean,
  user: User | null,
  tokens: AuthTokens | null,
  error: string | null,

  // Actions
  login: (credentials) => Promise<void>,
  logout: () => Promise<void>,
  refreshTokens: () => Promise<void>,
  hasRole: (role: string) => boolean,
  hasPermission: (permission: string) => boolean,
  clearError: () => void,
} = useAuth();
```

### Types

```typescript
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

## Sources

- [react-oidc-context](https://github.com/authts/react-oidc-context)
- [react-typescript-authentication-example](https://github.com/bezkoder/react-typescript-authentication-example)
- [Use React Context for Auth](https://dev.to/dayvster/use-react-context-for-auth-288g)
