# Express Middleware Chain Component

Standard Express.js middleware setup with CORS, Helmet, and rate limiting.

## Installation

```typescript
import { createMiddlewareChain, MiddlewareConfig } from './middleware';
```

## Usage

### Quick Start

```typescript
import express from 'express';
import { createMiddlewareChain } from '@library/middleware/express-chain';

const app = express();

// Create middleware chain with defaults
const middlewares = createMiddlewareChain({
  cors: {
    origins: ['https://myapp.com', 'http://localhost:3000'],
  },
  rateLimit: {
    windowMs: 60000,
    max: 100,
  },
  helmet: {
    contentSecurityPolicy: false, // Disable if causing issues
  },
});

// Apply all middlewares
middlewares.forEach(mw => app.use(mw));

// Your routes here
app.get('/api/data', (req, res) => {
  res.json({ message: 'Hello World' });
});
```

### Individual Middleware

```typescript
import {
  createCorsMiddleware,
  createRateLimitMiddleware,
  createHelmetMiddleware,
} from '@library/middleware/express-chain';

// CORS only
app.use(createCorsMiddleware({
  origins: ['https://trusted-domain.com'],
  credentials: true,
}));

// Rate limiting for specific routes
app.use('/api', createRateLimitMiddleware({
  windowMs: 60000,
  max: 30,
  skip: (req) => req.path === '/health',
}));

// Security headers
app.use(createHelmetMiddleware({
  hsts: { maxAge: 31536000, includeSubDomains: true },
  frameguard: { action: 'deny' },
}));
```

### Error Handler

```typescript
import { createErrorHandler } from '@library/middleware/express-chain';

// Must be last middleware
app.use(createErrorHandler());
```

## Configuration

### MiddlewareConfig

Main configuration for the middleware chain.

```typescript
interface MiddlewareConfig {
  cors?: CorsConfig | false;        // CORS settings (false to disable)
  rateLimit?: RateLimitConfig | false;  // Rate limiting settings
  helmet?: HelmetConfig | false;    // Security headers settings
  logging?: LoggingConfig | false;  // Request logging settings
  trustProxy?: boolean | number | string;  // Trust proxy setting
  bodyLimit?: string;               // Request body size limit
  compression?: boolean;            // Enable compression
}
```

### CorsConfig

```typescript
interface CorsConfig {
  origins?: (string | RegExp)[];  // Allowed origins
  methods?: string[];             // Allowed methods (default: GET, POST, PUT, PATCH, DELETE, OPTIONS)
  allowedHeaders?: string[];      // Allowed headers
  exposedHeaders?: string[];      // Headers exposed to client
  credentials?: boolean;          // Allow credentials (default: true)
  maxAge?: number;                // Preflight cache max age (default: 86400)
}
```

### RateLimitConfig

```typescript
interface RateLimitConfig {
  windowMs?: number;              // Time window in ms (default: 60000)
  max?: number;                   // Max requests per window (default: 100)
  message?: string | object;      // Rate limit exceeded message
  skip?: (req: Request) => boolean;  // Skip function
  keyGenerator?: (req: Request) => string;  // Custom key generator
  headers?: boolean;              // Enable rate limit headers (default: true)
}
```

### HelmetConfig

```typescript
interface HelmetConfig {
  contentSecurityPolicy?: boolean | object;
  dnsPrefetchControl?: boolean | { allow: boolean };
  frameguard?: boolean | { action: 'deny' | 'sameorigin' };
  hidePoweredBy?: boolean;
  hsts?: boolean | { maxAge: number; includeSubDomains: boolean };
  ieNoOpen?: boolean;
  noSniff?: boolean;
  referrerPolicy?: boolean | { policy: string };
  xssFilter?: boolean;
}
```

### LoggingConfig

```typescript
interface LoggingConfig {
  enabled?: boolean;              // Enable logging (default: true)
  logBody?: boolean;              // Log request body (default: false)
  skipPaths?: string[];           // Skip logging for these paths
  level?: 'debug' | 'info' | 'warn' | 'error';
}
```

## Examples

### Production Configuration

```typescript
const productionConfig: MiddlewareConfig = {
  cors: {
    origins: [process.env.FRONTEND_URL!],
    credentials: true,
    maxAge: 86400,
  },
  rateLimit: {
    windowMs: 60000,
    max: 100,
    skip: (req) => req.path === '/health',
    keyGenerator: (req) => req.headers['x-api-key'] as string || getClientIp(req),
  },
  helmet: {
    contentSecurityPolicy: {
      'default-src': "'self'",
      'script-src': "'self' 'unsafe-inline'",
      'style-src': "'self' 'unsafe-inline'",
    },
    hsts: {
      maxAge: 31536000,
      includeSubDomains: true,
    },
  },
  logging: {
    enabled: true,
    skipPaths: ['/health', '/metrics'],
  },
};
```

### Development Configuration

```typescript
const devConfig: MiddlewareConfig = {
  cors: {
    origins: ['http://localhost:3000', 'http://localhost:5173'],
    credentials: true,
  },
  rateLimit: false, // Disable in development
  helmet: {
    contentSecurityPolicy: false, // Often causes issues in dev
  },
  logging: {
    enabled: true,
    level: 'debug',
    logBody: true,
  },
};
```

### API-Only Configuration

```typescript
const apiConfig: MiddlewareConfig = {
  cors: false, // No CORS for internal APIs
  rateLimit: {
    windowMs: 1000,
    max: 10, // Strict rate limiting
  },
  helmet: {
    frameguard: { action: 'deny' },
  },
  logging: {
    enabled: true,
    skipPaths: ['/internal/health'],
  },
};
```

## Response Headers

The middleware chain sets the following headers:

| Header | Source | Description |
|--------|--------|-------------|
| `X-Request-ID` | Request ID | Unique request identifier |
| `X-RateLimit-Limit` | Rate Limit | Max requests per window |
| `X-RateLimit-Remaining` | Rate Limit | Remaining requests |
| `X-RateLimit-Reset` | Rate Limit | Window reset timestamp |
| `X-DNS-Prefetch-Control` | Helmet | DNS prefetch control |
| `X-Frame-Options` | Helmet | Clickjacking protection |
| `X-Content-Type-Options` | Helmet | MIME type sniffing |
| `X-XSS-Protection` | Helmet | XSS filter |
| `Strict-Transport-Security` | Helmet | HTTPS enforcement |
| `Referrer-Policy` | Helmet | Referrer header control |

## Source

Patterns inspired by:
- `nsbu-rpg-app/src/middleware.ts` - Next.js auth middleware
- `nsbu-rpg-app/src/lib/socket-server.ts` - Socket.io rate limiting
- Common Express.js security patterns

## Notes

- Rate limiting uses in-memory store. For production clusters, use Redis.
- CORS middleware handles preflight OPTIONS requests automatically.
- Error handler hides stack traces in production.
- Request IDs enable distributed tracing across services.
