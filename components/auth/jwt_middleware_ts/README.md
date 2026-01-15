# JWT Middleware for Express (TypeScript)

Production-ready JWT authentication middleware using the jose library.

## Features

- Access and refresh token support with rotation
- Role-based authorization middleware
- Optional authentication for public endpoints
- Type-safe with full TypeScript support
- Token revocation via JTI tracking
- Secure key generation utilities

## Installation

```bash
npm install jose express @types/express
```

## Quick Start

```typescript
import express from 'express';
import {
  JWTAuth,
  authenticate,
  requireRole,
  AuthenticatedRequest
} from '@library/auth/jwt-middleware-ts';

const app = express();

// Initialize with secure key from environment
const auth = new JWTAuth({
  secretKey: process.env.JWT_SECRET!, // Min 32 chars
  issuer: 'my-app',
  audience: 'my-app-users',
  accessTokenExpireSeconds: 900,     // 15 minutes
  refreshTokenExpireSeconds: 604800  // 7 days
});

// Login endpoint
app.post('/auth/login', async (req, res) => {
  // Validate credentials...
  const user = await validateUser(req.body);

  // Create token pair
  const tokens = await auth.createTokenPair({
    sub: user.id,
    email: user.email,
    name: user.name,
    role: user.role
  });

  res.json(tokens);
});

// Protected route
app.get('/api/profile', authenticate(auth), (req, res) => {
  const authReq = req as AuthenticatedRequest;
  res.json({ user: authReq.user });
});

// Admin-only route
app.get('/api/admin/users',
  authenticate(auth),
  requireRole('admin'),
  (req, res) => {
    res.json({ admin: true });
  }
);

// Multiple roles allowed
app.get('/api/staff/dashboard',
  authenticate(auth),
  requireRole(['admin', 'manager']),
  (req, res) => {
    res.json({ staff: true });
  }
);

// Optional auth (public with user context)
app.get('/api/posts',
  authenticate(auth, { required: false }),
  (req, res) => {
    const authReq = req as AuthenticatedRequest;
    if (authReq.user) {
      // Return personalized content
    }
    res.json({ posts: [] });
  }
);

// Refresh token endpoint
app.post('/auth/refresh', async (req, res) => {
  const { refreshToken } = req.body;

  // Option 1: Just get new access token
  const newAccessToken = await auth.refreshAccessToken(refreshToken);

  // Option 2: Rotate (new access + new refresh)
  const newTokens = await auth.rotateRefreshToken(refreshToken);

  if (!newTokens) {
    return res.status(401).json({ error: 'Invalid refresh token' });
  }

  // Store old JTI in revocation list
  const oldJti = await auth.getJtiFromToken(refreshToken);

  res.json(newTokens);
});
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `secretKey` | string | required | HMAC signing key (min 32 chars) |
| `algorithm` | string | 'HS256' | JWT algorithm (HS256/HS384/HS512) |
| `issuer` | string | - | Token issuer claim |
| `audience` | string | - | Token audience claim |
| `accessTokenExpireSeconds` | number | 900 | Access token lifetime (15 min) |
| `refreshTokenExpireSeconds` | number | 604800 | Refresh token lifetime (7 days) |

## API Reference

### JWTAuth Class

```typescript
// Create access token
const token = await auth.createAccessToken({
  sub: 'user-123',
  email: 'user@example.com',
  role: 'admin'
});

// Create refresh token
const refreshToken = await auth.createRefreshToken({ sub: 'user-123' });

// Create both at once
const { accessToken, refreshToken, expiresIn } = await auth.createTokenPair({
  sub: 'user-123'
});

// Verify token
const payload = await auth.verifyToken(token, 'access');

// Get user from token
const user = await auth.getUserFromToken(token);

// Refresh access token
const newAccess = await auth.refreshAccessToken(refreshToken);

// Rotate refresh token (returns new pair)
const newPair = await auth.rotateRefreshToken(refreshToken);

// Get JTI for revocation
const jti = await auth.getJtiFromToken(refreshToken);
```

### Middleware

```typescript
// Required authentication
app.get('/protected', authenticate(auth), handler);

// Optional authentication
app.get('/public', authenticate(auth, { required: false }), handler);

// With custom error handler
app.get('/api', authenticate(auth, {
  onError: (error, req) => {
    console.log(`Auth failed: ${error.message}`);
  }
}), handler);

// Role-based access
app.get('/admin', authenticate(auth), requireRole('admin'), handler);
app.get('/staff', authenticate(auth), requireRole(['admin', 'manager']), handler);
```

### Utilities

```typescript
import { generateSecureToken, generateApiKey } from '@library/auth/jwt-middleware-ts';

// Generate secure random token
const sessionToken = generateSecureToken(32);

// Generate API key with prefix
const apiKey = generateApiKey('sk'); // sk_abc123...
const publicKey = generateApiKey('pk'); // pk_xyz789...
```

## Security Best Practices

1. **Secret Key**: Use `generateSecureToken(32)` or longer for production keys
2. **Environment Variables**: Never hardcode secrets in source code
3. **Key Rotation**: Rotate JWT secrets every 90 days
4. **HTTPS Only**: Always transmit tokens over HTTPS
5. **Token Storage**: Store refresh tokens server-side when possible
6. **Revocation**: Track JTIs in a database for token revocation

## Token Structure

### Access Token Claims
- `sub`: Subject (user ID)
- `email`: User email
- `name`: User display name
- `role`: User role
- `type`: "access"
- `iat`: Issued at timestamp
- `exp`: Expiration timestamp
- `iss`: Issuer (if configured)
- `aud`: Audience (if configured)

### Refresh Token Claims
- All access token claims, plus:
- `jti`: Unique token ID for revocation

## Integration with Existing Library

This component integrates with `security/jwt-auth` (Python) for consistent JWT handling across TypeScript and Python services.

```typescript
// TypeScript Express service
const auth = new JWTAuth({
  secretKey: process.env.JWT_SECRET!,
  issuer: 'shared-issuer',
  audience: 'shared-audience'
});

// Python FastAPI service (using security/jwt-auth)
// Same secret, issuer, audience = cross-service auth
```
