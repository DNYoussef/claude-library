/**
 * JWT Middleware Types
 *
 * Type definitions for Express JWT authentication middleware.
 * Uses jose library for JWT operations.
 *
 * LEGO Component: auth/jwt-middleware-ts
 */

import { Request } from 'express';

/**
 * JWT Configuration options
 */
export interface JWTConfig {
  /**
   * Secret key for signing/verifying tokens.
   * MUST be at least 32 bytes for HS256 security.
   * Use environment variables: process.env.JWT_SECRET
   */
  secretKey: string;

  /**
   * JWT signing algorithm (default: HS256)
   */
  algorithm?: 'HS256' | 'HS384' | 'HS512';

  /**
   * Token issuer claim (optional)
   */
  issuer?: string;

  /**
   * Token audience claim (optional)
   */
  audience?: string;

  /**
   * Access token expiration in seconds (default: 900 = 15 minutes)
   */
  accessTokenExpireSeconds?: number;

  /**
   * Refresh token expiration in seconds (default: 604800 = 7 days)
   */
  refreshTokenExpireSeconds?: number;
}

/**
 * Standard JWT payload structure
 */
export interface JWTPayload {
  /** Subject - typically user ID */
  sub: string;

  /** Email address */
  email?: string;

  /** User display name */
  name?: string | null;

  /** User role for authorization */
  role?: string;

  /** Token type: 'access' or 'refresh' */
  type?: 'access' | 'refresh';

  /** Issued at timestamp */
  iat?: number;

  /** Expiration timestamp */
  exp?: number;

  /** JWT ID for token revocation */
  jti?: string;

  /** Issuer */
  iss?: string;

  /** Audience */
  aud?: string;

  /** Additional custom claims */
  [key: string]: unknown;
}

/**
 * Verified user from JWT token
 */
export interface VerifiedUser {
  id: string;
  email: string;
  name: string | null;
  role: string;
}

/**
 * Extended Express Request with authenticated user
 */
export interface AuthenticatedRequest extends Request {
  user: VerifiedUser;
  token: string;
}

/**
 * Options for authentication middleware
 */
export interface AuthMiddlewareOptions {
  /**
   * Require authentication (return 401 if not authenticated)
   * Default: true
   */
  required?: boolean;

  /**
   * Required role(s) for authorization
   */
  roles?: string | string[];

  /**
   * Custom error handler
   */
  onError?: (error: AuthError, req: Request) => void;
}

/**
 * Authentication error types
 */
export type AuthErrorType =
  | 'MISSING_TOKEN'
  | 'INVALID_TOKEN'
  | 'EXPIRED_TOKEN'
  | 'INVALID_TYPE'
  | 'INSUFFICIENT_ROLE'
  | 'USER_NOT_FOUND';

/**
 * Authentication error
 */
export class AuthError extends Error {
  constructor(
    public readonly type: AuthErrorType,
    message: string,
    public readonly statusCode: number = 401
  ) {
    super(message);
    this.name = 'AuthError';
  }

  static missingToken(): AuthError {
    return new AuthError('MISSING_TOKEN', 'Authorization header missing', 401);
  }

  static invalidToken(): AuthError {
    return new AuthError('INVALID_TOKEN', 'Invalid or malformed token', 401);
  }

  static expiredToken(): AuthError {
    return new AuthError('EXPIRED_TOKEN', 'Token has expired', 401);
  }

  static invalidType(expected: string): AuthError {
    return new AuthError('INVALID_TYPE', `Expected ${expected} token`, 401);
  }

  static insufficientRole(required: string | string[]): AuthError {
    const roles = Array.isArray(required) ? required.join(', ') : required;
    return new AuthError('INSUFFICIENT_ROLE', `Required role(s): ${roles}`, 403);
  }

  toJSON(): Record<string, unknown> {
    return {
      error: this.type,
      message: this.message,
      statusCode: this.statusCode,
    };
  }
}

/**
 * Token creation options
 */
export interface TokenOptions {
  /** Custom expiration override */
  expiresIn?: number;

  /** Additional claims to include */
  claims?: Record<string, unknown>;
}

/**
 * Token pair (access + refresh)
 */
export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}
