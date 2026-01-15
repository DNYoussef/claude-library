/**
 * JWT Authentication Middleware for Express
 *
 * Production-ready JWT middleware using jose library.
 * Supports access/refresh tokens, role-based access, and optional auth.
 *
 * LEGO Component: auth/jwt-middleware-ts
 *
 * @example
 * ```typescript
 * import { JWTAuth, authenticate, requireRole } from './middleware';
 *
 * // Initialize
 * const auth = new JWTAuth({ secretKey: process.env.JWT_SECRET! });
 *
 * // Protect routes
 * app.get('/protected', authenticate(auth), (req, res) => {
 *   res.json({ user: req.user });
 * });
 *
 * // Role-based access
 * app.get('/admin', authenticate(auth), requireRole('admin'), (req, res) => {
 *   res.json({ admin: true });
 * });
 * ```
 */

import { Request, Response, NextFunction, RequestHandler } from 'express';
import * as jose from 'jose';
import crypto from 'crypto';
import {
  JWTConfig,
  JWTPayload,
  VerifiedUser,
  AuthenticatedRequest,
  AuthMiddlewareOptions,
  AuthError,
  TokenOptions,
  TokenPair,
} from './types';

// Minimum secret key length for HS256 security (32 bytes = 256 bits)
const MIN_SECRET_KEY_LENGTH = 32;

/**
 * JWT Authentication Manager
 *
 * Handles token creation, verification, and middleware generation.
 * Thread-safe and suitable for production use.
 */
export class JWTAuth {
  private readonly config: Required<JWTConfig>;
  private readonly secretKey: Uint8Array;

  constructor(config: JWTConfig) {
    // Validate secret key
    if (!config.secretKey) {
      throw new Error('secretKey is required');
    }
    if (config.secretKey.length < MIN_SECRET_KEY_LENGTH) {
      throw new Error(
        `secretKey must be at least ${MIN_SECRET_KEY_LENGTH} characters for ${config.algorithm || 'HS256'} security`
      );
    }

    // Set defaults
    this.config = {
      secretKey: config.secretKey,
      algorithm: config.algorithm || 'HS256',
      issuer: config.issuer || '',
      audience: config.audience || '',
      accessTokenExpireSeconds: config.accessTokenExpireSeconds || 900, // 15 min
      refreshTokenExpireSeconds: config.refreshTokenExpireSeconds || 604800, // 7 days
    };

    // Encode secret key for jose
    this.secretKey = new TextEncoder().encode(this.config.secretKey);
  }

  /**
   * Create an access token
   *
   * @param payload - Token payload with user data
   * @param options - Optional token configuration
   * @returns Signed JWT access token
   */
  async createAccessToken(
    payload: Partial<JWTPayload>,
    options?: TokenOptions
  ): Promise<string> {
    const now = Math.floor(Date.now() / 1000);
    const expiresIn = options?.expiresIn || this.config.accessTokenExpireSeconds;

    const claims: JWTPayload = {
      ...payload,
      ...options?.claims,
      type: 'access',
      iat: now,
      exp: now + expiresIn,
    };

    // Add optional claims
    if (this.config.issuer) {
      claims.iss = this.config.issuer;
    }
    if (this.config.audience) {
      claims.aud = this.config.audience;
    }

    return await new jose.SignJWT(claims as jose.JWTPayload)
      .setProtectedHeader({ alg: this.config.algorithm })
      .sign(this.secretKey);
  }

  /**
   * Create a refresh token
   *
   * @param payload - Token payload with user data
   * @param options - Optional token configuration
   * @returns Signed JWT refresh token with JTI for revocation
   */
  async createRefreshToken(
    payload: Partial<JWTPayload>,
    options?: TokenOptions
  ): Promise<string> {
    const now = Math.floor(Date.now() / 1000);
    const expiresIn = options?.expiresIn || this.config.refreshTokenExpireSeconds;

    const claims: JWTPayload = {
      ...payload,
      ...options?.claims,
      type: 'refresh',
      iat: now,
      exp: now + expiresIn,
      jti: crypto.randomBytes(32).toString('base64url'), // Unique ID for revocation
    };

    // Add optional claims
    if (this.config.issuer) {
      claims.iss = this.config.issuer;
    }
    if (this.config.audience) {
      claims.aud = this.config.audience;
    }

    return await new jose.SignJWT(claims as jose.JWTPayload)
      .setProtectedHeader({ alg: this.config.algorithm })
      .sign(this.secretKey);
  }

  /**
   * Create both access and refresh tokens
   *
   * @param payload - Token payload with user data
   * @returns Token pair with access, refresh, and expiry info
   */
  async createTokenPair(payload: Partial<JWTPayload>): Promise<TokenPair> {
    const [accessToken, refreshToken] = await Promise.all([
      this.createAccessToken(payload),
      this.createRefreshToken(payload),
    ]);

    return {
      accessToken,
      refreshToken,
      expiresIn: this.config.accessTokenExpireSeconds,
    };
  }

  /**
   * Verify and decode a JWT token
   *
   * @param token - JWT token string
   * @param expectedType - Expected token type ('access' or 'refresh')
   * @returns Decoded payload or null if invalid
   */
  async verifyToken(
    token: string,
    expectedType: 'access' | 'refresh' = 'access'
  ): Promise<JWTPayload | null> {
    try {
      const options: jose.JWTVerifyOptions = {
        algorithms: [this.config.algorithm],
      };

      // Add optional verification
      if (this.config.issuer) {
        options.issuer = this.config.issuer;
      }
      if (this.config.audience) {
        options.audience = this.config.audience;
      }

      const { payload } = await jose.jwtVerify(token, this.secretKey, options);

      // Verify token type to prevent confusion attacks
      if (payload.type !== expectedType) {
        return null;
      }

      return payload as JWTPayload;
    } catch {
      return null;
    }
  }

  /**
   * Extract user info from a verified token
   *
   * @param token - JWT token string
   * @returns VerifiedUser or null if invalid
   */
  async getUserFromToken(token: string): Promise<VerifiedUser | null> {
    const payload = await this.verifyToken(token, 'access');
    if (!payload || !payload.sub) {
      return null;
    }

    return {
      id: payload.sub,
      email: payload.email || '',
      name: payload.name || null,
      role: payload.role || 'user',
    };
  }

  /**
   * Refresh an access token using a valid refresh token
   *
   * @param refreshToken - Valid refresh token
   * @returns New access token or null if refresh token invalid
   */
  async refreshAccessToken(refreshToken: string): Promise<string | null> {
    const payload = await this.verifyToken(refreshToken, 'refresh');
    if (!payload) {
      return null;
    }

    // Extract subject and preserve custom claims
    const { sub, email, name, role, ...rest } = payload;

    // Filter out JWT-specific claims
    const customClaims: Record<string, unknown> = {};
    const excludedKeys = ['type', 'iat', 'exp', 'jti', 'iss', 'aud'];
    for (const [key, value] of Object.entries(rest)) {
      if (!excludedKeys.includes(key)) {
        customClaims[key] = value;
      }
    }

    return await this.createAccessToken({
      sub,
      email,
      name,
      role,
      ...customClaims,
    });
  }

  /**
   * Rotate refresh token: create new access + refresh pair
   *
   * @param refreshToken - Valid refresh token
   * @returns New token pair or null if refresh token invalid
   *
   * @security Store the old JTI in a revocation list after calling this
   */
  async rotateRefreshToken(refreshToken: string): Promise<TokenPair | null> {
    const payload = await this.verifyToken(refreshToken, 'refresh');
    if (!payload) {
      return null;
    }

    // Extract claims
    const { sub, email, name, role, ...rest } = payload;

    // Filter out JWT-specific claims
    const customClaims: Record<string, unknown> = {};
    const excludedKeys = ['type', 'iat', 'exp', 'jti', 'iss', 'aud'];
    for (const [key, value] of Object.entries(rest)) {
      if (!excludedKeys.includes(key)) {
        customClaims[key] = value;
      }
    }

    return await this.createTokenPair({
      sub,
      email,
      name,
      role,
      ...customClaims,
    });
  }

  /**
   * Extract JTI from a refresh token for revocation tracking
   *
   * @param refreshToken - Refresh token
   * @returns JTI string or null
   */
  async getJtiFromToken(refreshToken: string): Promise<string | null> {
    const payload = await this.verifyToken(refreshToken, 'refresh');
    return payload?.jti || null;
  }
}

/**
 * Extract Bearer token from Authorization header
 */
function extractBearerToken(req: Request): string | null {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }
  return authHeader.slice(7);
}

/**
 * Authentication middleware factory
 *
 * @param auth - JWTAuth instance
 * @param options - Middleware options
 * @returns Express middleware
 *
 * @example
 * ```typescript
 * // Required authentication
 * app.get('/protected', authenticate(auth), handler);
 *
 * // Optional authentication
 * app.get('/public', authenticate(auth, { required: false }), handler);
 * ```
 */
export function authenticate(
  auth: JWTAuth,
  options: AuthMiddlewareOptions = {}
): RequestHandler {
  const { required = true, onError } = options;

  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const token = extractBearerToken(req);

      if (!token) {
        if (required) {
          const error = AuthError.missingToken();
          onError?.(error, req);
          res.status(error.statusCode).json(error.toJSON());
          return;
        }
        // Optional auth - continue without user
        next();
        return;
      }

      const user = await auth.getUserFromToken(token);

      if (!user) {
        if (required) {
          const error = AuthError.invalidToken();
          onError?.(error, req);
          res.status(error.statusCode).json(error.toJSON());
          return;
        }
        // Optional auth - continue without user
        next();
        return;
      }

      // Attach user and token to request
      (req as AuthenticatedRequest).user = user;
      (req as AuthenticatedRequest).token = token;

      next();
    } catch (err) {
      const error = AuthError.invalidToken();
      onError?.(error, req);
      res.status(error.statusCode).json(error.toJSON());
    }
  };
}

/**
 * Role-based authorization middleware
 *
 * Must be used AFTER authenticate middleware.
 *
 * @param roles - Required role(s)
 * @returns Express middleware
 *
 * @example
 * ```typescript
 * // Single role
 * app.get('/admin', authenticate(auth), requireRole('admin'), handler);
 *
 * // Multiple roles (any match)
 * app.get('/staff', authenticate(auth), requireRole(['admin', 'manager']), handler);
 * ```
 */
export function requireRole(roles: string | string[]): RequestHandler {
  const allowedRoles = Array.isArray(roles) ? roles : [roles];

  return (req: Request, res: Response, next: NextFunction): void => {
    const authReq = req as AuthenticatedRequest;

    if (!authReq.user) {
      const error = AuthError.missingToken();
      res.status(error.statusCode).json(error.toJSON());
      return;
    }

    if (!allowedRoles.includes(authReq.user.role)) {
      const error = AuthError.insufficientRole(roles);
      res.status(error.statusCode).json(error.toJSON());
      return;
    }

    next();
  };
}

/**
 * Generate a cryptographically secure token
 *
 * @param length - Token length in bytes (default: 32)
 * @returns URL-safe base64 encoded token
 */
export function generateSecureToken(length: number = 32): string {
  return crypto.randomBytes(length).toString('base64url');
}

/**
 * Generate an API key with prefix
 *
 * @param prefix - Key prefix (default: 'sk')
 * @returns Prefixed API key (e.g., 'sk_abc123...')
 */
export function generateApiKey(prefix: string = 'sk'): string {
  return `${prefix}_${generateSecureToken(32)}`;
}
