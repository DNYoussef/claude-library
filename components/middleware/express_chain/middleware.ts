/**
 * Express Middleware Chain Component
 *
 * Standard Express.js middleware setup with CORS, Helmet, and rate limiting.
 * TypeScript component with consistent interface patterns.
 *
 * Usage:
 *   import { createMiddlewareChain, MiddlewareConfig } from './middleware';
 *
 *   const config: MiddlewareConfig = {
 *     cors: { origins: ['https://example.com'] },
 *     rateLimit: { windowMs: 60000, max: 100 },
 *     helmet: { contentSecurityPolicy: false },
 *   };
 *
 *   const middlewares = createMiddlewareChain(config);
 *   middlewares.forEach(mw => app.use(mw));
 */

import type { Request, Response, NextFunction, RequestHandler } from 'express';

// =============================================================================
// TYPES AND INTERFACES
// =============================================================================

/**
 * CORS configuration options.
 */
export interface CorsConfig {
  /** Allowed origins (strings or regex patterns) */
  origins?: (string | RegExp)[];
  /** Allowed HTTP methods */
  methods?: string[];
  /** Allowed headers */
  allowedHeaders?: string[];
  /** Headers exposed to client */
  exposedHeaders?: string[];
  /** Allow credentials (cookies, auth headers) */
  credentials?: boolean;
  /** Preflight cache max age in seconds */
  maxAge?: number;
}

/**
 * Rate limiter configuration options.
 */
export interface RateLimitConfig {
  /** Time window in milliseconds */
  windowMs?: number;
  /** Max requests per window */
  max?: number;
  /** Custom message for rate limit exceeded */
  message?: string | object;
  /** Skip rate limiting for certain requests */
  skip?: (req: Request) => boolean;
  /** Custom key generator for rate limiting */
  keyGenerator?: (req: Request) => string;
  /** Enable rate limit headers */
  headers?: boolean;
}

/**
 * Security headers (Helmet) configuration.
 */
export interface HelmetConfig {
  /** Content Security Policy options (false to disable) */
  contentSecurityPolicy?: boolean | object;
  /** X-DNS-Prefetch-Control header */
  dnsPrefetchControl?: boolean | { allow: boolean };
  /** Expect-CT header */
  expectCt?: boolean | { enforce: boolean; maxAge: number };
  /** X-Frame-Options header */
  frameguard?: boolean | { action: 'deny' | 'sameorigin' };
  /** Hide X-Powered-By header */
  hidePoweredBy?: boolean;
  /** Strict-Transport-Security header */
  hsts?: boolean | { maxAge: number; includeSubDomains: boolean };
  /** X-Download-Options header */
  ieNoOpen?: boolean;
  /** X-Content-Type-Options header */
  noSniff?: boolean;
  /** X-Permitted-Cross-Domain-Policies header */
  permittedCrossDomainPolicies?: boolean | { permittedPolicies: string };
  /** Referrer-Policy header */
  referrerPolicy?: boolean | { policy: string };
  /** X-XSS-Protection header */
  xssFilter?: boolean;
}

/**
 * Request logging configuration.
 */
export interface LoggingConfig {
  /** Enable request logging */
  enabled?: boolean;
  /** Log request body */
  logBody?: boolean;
  /** Skip logging for certain paths */
  skipPaths?: string[];
  /** Log level */
  level?: 'debug' | 'info' | 'warn' | 'error';
}

/**
 * Main middleware chain configuration.
 */
export interface MiddlewareConfig {
  cors?: CorsConfig | false;
  rateLimit?: RateLimitConfig | false;
  helmet?: HelmetConfig | false;
  logging?: LoggingConfig | false;
  /** Trust proxy setting (for rate limiter behind reverse proxy) */
  trustProxy?: boolean | number | string;
  /** Request size limit for body parser */
  bodyLimit?: string;
  /** Enable compression */
  compression?: boolean;
}

/**
 * Rate limit store entry.
 */
interface RateLimitEntry {
  count: number;
  resetTime: number;
}

// =============================================================================
// DEFAULT CONFIGURATIONS
// =============================================================================

const DEFAULT_CORS: CorsConfig = {
  origins: ['http://localhost:3000'],
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
  exposedHeaders: ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset'],
  credentials: true,
  maxAge: 86400, // 24 hours
};

const DEFAULT_RATE_LIMIT: Required<Omit<RateLimitConfig, 'skip' | 'keyGenerator'>> = {
  windowMs: 60 * 1000, // 1 minute
  max: 100,
  message: { error: 'rate_limited', message: 'Too many requests, please try again later' },
  headers: true,
};

const DEFAULT_HELMET: HelmetConfig = {
  contentSecurityPolicy: true,
  dnsPrefetchControl: { allow: false },
  frameguard: { action: 'deny' },
  hidePoweredBy: true,
  hsts: { maxAge: 31536000, includeSubDomains: true },
  ieNoOpen: true,
  noSniff: true,
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
  xssFilter: true,
};

const DEFAULT_LOGGING: Required<LoggingConfig> = {
  enabled: true,
  logBody: false,
  skipPaths: ['/health', '/metrics', '/favicon.ico'],
  level: 'info',
};

// =============================================================================
// MIDDLEWARE IMPLEMENTATIONS
// =============================================================================

/**
 * Create CORS middleware.
 *
 * @param config - CORS configuration
 * @returns Express middleware function
 */
export function createCorsMiddleware(config: CorsConfig = {}): RequestHandler {
  const options = { ...DEFAULT_CORS, ...config };

  return (req: Request, res: Response, next: NextFunction): void => {
    const origin = req.headers.origin;

    // Check if origin is allowed
    let isAllowed = false;
    if (origin) {
      isAllowed = options.origins?.some((allowed) => {
        if (typeof allowed === 'string') {
          return allowed === origin || allowed === '*';
        }
        return allowed.test(origin);
      }) ?? false;
    }

    if (isAllowed && origin) {
      res.setHeader('Access-Control-Allow-Origin', origin);
    }

    if (options.credentials) {
      res.setHeader('Access-Control-Allow-Credentials', 'true');
    }

    if (options.exposedHeaders?.length) {
      res.setHeader('Access-Control-Expose-Headers', options.exposedHeaders.join(', '));
    }

    // Handle preflight requests
    if (req.method === 'OPTIONS') {
      if (options.methods?.length) {
        res.setHeader('Access-Control-Allow-Methods', options.methods.join(', '));
      }
      if (options.allowedHeaders?.length) {
        res.setHeader('Access-Control-Allow-Headers', options.allowedHeaders.join(', '));
      }
      if (options.maxAge) {
        res.setHeader('Access-Control-Max-Age', String(options.maxAge));
      }
      res.status(204).end();
      return;
    }

    next();
  };
}

/**
 * Create rate limiting middleware.
 *
 * Uses in-memory store. For production, consider Redis store.
 *
 * @param config - Rate limit configuration
 * @returns Express middleware function
 */
export function createRateLimitMiddleware(config: RateLimitConfig = {}): RequestHandler {
  const options = { ...DEFAULT_RATE_LIMIT, ...config };
  const store = new Map<string, RateLimitEntry>();

  // Cleanup old entries periodically
  setInterval(() => {
    const now = Date.now();
    for (const [key, entry] of store.entries()) {
      if (entry.resetTime < now) {
        store.delete(key);
      }
    }
  }, options.windowMs);

  return (req: Request, res: Response, next: NextFunction): void => {
    // Check skip function
    if (config.skip?.(req)) {
      next();
      return;
    }

    // Generate key (default: IP address)
    const key = config.keyGenerator?.(req) ?? getClientIp(req);
    const now = Date.now();

    // Get or create entry
    let entry = store.get(key);
    if (!entry || entry.resetTime < now) {
      entry = {
        count: 0,
        resetTime: now + options.windowMs,
      };
      store.set(key, entry);
    }

    entry.count++;

    // Set rate limit headers
    if (options.headers) {
      res.setHeader('X-RateLimit-Limit', String(options.max));
      res.setHeader('X-RateLimit-Remaining', String(Math.max(0, options.max - entry.count)));
      res.setHeader('X-RateLimit-Reset', String(Math.ceil(entry.resetTime / 1000)));
    }

    // Check if over limit
    if (entry.count > options.max) {
      res.setHeader('Retry-After', String(Math.ceil((entry.resetTime - now) / 1000)));
      res.status(429).json(options.message);
      return;
    }

    next();
  };
}

/**
 * Create security headers middleware (Helmet-like).
 *
 * @param config - Security headers configuration
 * @returns Express middleware function
 */
export function createHelmetMiddleware(config: HelmetConfig = {}): RequestHandler {
  const options = { ...DEFAULT_HELMET, ...config };

  return (_req: Request, res: Response, next: NextFunction): void => {
    // Hide X-Powered-By
    if (options.hidePoweredBy) {
      res.removeHeader('X-Powered-By');
    }

    // X-DNS-Prefetch-Control
    if (options.dnsPrefetchControl !== false) {
      const allow = typeof options.dnsPrefetchControl === 'object'
        ? options.dnsPrefetchControl.allow
        : false;
      res.setHeader('X-DNS-Prefetch-Control', allow ? 'on' : 'off');
    }

    // X-Frame-Options
    if (options.frameguard !== false) {
      const action = typeof options.frameguard === 'object'
        ? options.frameguard.action.toUpperCase()
        : 'DENY';
      res.setHeader('X-Frame-Options', action);
    }

    // Strict-Transport-Security
    if (options.hsts !== false) {
      const hstsConfig = typeof options.hsts === 'object'
        ? options.hsts
        : { maxAge: 31536000, includeSubDomains: true };
      let value = `max-age=${hstsConfig.maxAge}`;
      if (hstsConfig.includeSubDomains) {
        value += '; includeSubDomains';
      }
      res.setHeader('Strict-Transport-Security', value);
    }

    // X-Download-Options
    if (options.ieNoOpen !== false) {
      res.setHeader('X-Download-Options', 'noopen');
    }

    // X-Content-Type-Options
    if (options.noSniff !== false) {
      res.setHeader('X-Content-Type-Options', 'nosniff');
    }

    // Referrer-Policy
    if (options.referrerPolicy !== false) {
      const policy = typeof options.referrerPolicy === 'object'
        ? options.referrerPolicy.policy
        : 'strict-origin-when-cross-origin';
      res.setHeader('Referrer-Policy', policy);
    }

    // X-XSS-Protection
    if (options.xssFilter !== false) {
      res.setHeader('X-XSS-Protection', '1; mode=block');
    }

    // Content-Security-Policy
    if (options.contentSecurityPolicy !== false && options.contentSecurityPolicy !== true) {
      // Custom CSP provided
      if (typeof options.contentSecurityPolicy === 'object') {
        const directives = Object.entries(options.contentSecurityPolicy)
          .map(([key, value]) => `${key} ${value}`)
          .join('; ');
        res.setHeader('Content-Security-Policy', directives);
      }
    } else if (options.contentSecurityPolicy === true) {
      // Default restrictive CSP
      res.setHeader('Content-Security-Policy', "default-src 'self'");
    }

    next();
  };
}

/**
 * Create request logging middleware.
 *
 * @param config - Logging configuration
 * @returns Express middleware function
 */
export function createLoggingMiddleware(config: LoggingConfig = {}): RequestHandler {
  const options = { ...DEFAULT_LOGGING, ...config };

  return (req: Request, res: Response, next: NextFunction): void => {
    if (!options.enabled) {
      next();
      return;
    }

    // Skip configured paths
    if (options.skipPaths?.some((path) => req.path.startsWith(path))) {
      next();
      return;
    }

    const startTime = Date.now();
    const requestId = req.headers['x-request-id'] as string || generateRequestId();

    // Add request ID to response headers
    res.setHeader('X-Request-ID', requestId);

    // Capture response finish
    res.on('finish', () => {
      const duration = Date.now() - startTime;
      const logData = {
        method: req.method,
        path: req.path,
        statusCode: res.statusCode,
        duration: `${duration}ms`,
        requestId,
        userAgent: req.headers['user-agent'],
        ip: getClientIp(req),
      };

      // Log based on status code
      const logFn = res.statusCode >= 500 ? console.error
        : res.statusCode >= 400 ? console.warn
        : console.log;

      logFn(`[${options.level?.toUpperCase()}]`, JSON.stringify(logData));
    });

    next();
  };
}

/**
 * Create request ID middleware.
 *
 * Ensures every request has a unique ID for tracing.
 *
 * @returns Express middleware function
 */
export function createRequestIdMiddleware(): RequestHandler {
  return (req: Request, res: Response, next: NextFunction): void => {
    const requestId = req.headers['x-request-id'] as string || generateRequestId();
    req.headers['x-request-id'] = requestId;
    res.setHeader('X-Request-ID', requestId);
    next();
  };
}

// =============================================================================
// MIDDLEWARE CHAIN FACTORY
// =============================================================================

/**
 * Create a chain of middleware based on configuration.
 *
 * @param config - Middleware chain configuration
 * @returns Array of Express middleware functions
 *
 * @example
 * const middlewares = createMiddlewareChain({
 *   cors: { origins: ['https://myapp.com'] },
 *   rateLimit: { max: 50 },
 *   helmet: { contentSecurityPolicy: false },
 * });
 *
 * middlewares.forEach(mw => app.use(mw));
 */
export function createMiddlewareChain(config: MiddlewareConfig = {}): RequestHandler[] {
  const middlewares: RequestHandler[] = [];

  // Request ID (always first)
  middlewares.push(createRequestIdMiddleware());

  // Security headers
  if (config.helmet !== false) {
    middlewares.push(createHelmetMiddleware(config.helmet || {}));
  }

  // CORS
  if (config.cors !== false) {
    middlewares.push(createCorsMiddleware(config.cors || {}));
  }

  // Rate limiting
  if (config.rateLimit !== false) {
    middlewares.push(createRateLimitMiddleware(config.rateLimit || {}));
  }

  // Logging
  if (config.logging !== false) {
    middlewares.push(createLoggingMiddleware(config.logging || {}));
  }

  return middlewares;
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get client IP address from request.
 *
 * Handles X-Forwarded-For header for reverse proxies.
 *
 * @param req - Express request
 * @returns Client IP address
 */
export function getClientIp(req: Request): string {
  const forwardedFor = req.headers['x-forwarded-for'];
  if (forwardedFor) {
    const ips = Array.isArray(forwardedFor)
      ? forwardedFor[0]
      : forwardedFor.split(',')[0];
    return ips.trim();
  }
  return req.socket?.remoteAddress || req.ip || 'unknown';
}

/**
 * Generate unique request ID.
 *
 * @returns UUID-like string
 */
export function generateRequestId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 10);
  return `${timestamp}-${random}`;
}

/**
 * Create error handler middleware.
 *
 * Catches unhandled errors and returns consistent error response.
 *
 * @returns Express error middleware
 */
export function createErrorHandler(): (
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) => void {
  return (err: Error, req: Request, res: Response, _next: NextFunction): void => {
    const requestId = req.headers['x-request-id'] as string;

    console.error(`[ERROR] ${requestId}:`, err);

    // Don't leak error details in production
    const isProduction = process.env.NODE_ENV === 'production';

    res.status(500).json({
      error: 'internal_error',
      message: isProduction ? 'An internal error occurred' : err.message,
      requestId,
      ...(isProduction ? {} : { stack: err.stack }),
    });
  };
}
