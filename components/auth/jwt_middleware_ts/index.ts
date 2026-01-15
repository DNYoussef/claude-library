/**
 * JWT Middleware for Express
 *
 * Production-ready JWT authentication middleware using jose library.
 *
 * LEGO Component: auth/jwt-middleware-ts
 *
 * @example
 * ```typescript
 * import {
 *   JWTAuth,
 *   authenticate,
 *   requireRole,
 *   generateSecureToken
 * } from '@library/auth/jwt-middleware-ts';
 *
 * // Initialize with secure key from environment
 * const auth = new JWTAuth({
 *   secretKey: process.env.JWT_SECRET!,
 *   issuer: 'my-app',
 *   accessTokenExpireSeconds: 900,  // 15 minutes
 *   refreshTokenExpireSeconds: 604800  // 7 days
 * });
 *
 * // Create tokens on login
 * const tokens = await auth.createTokenPair({
 *   sub: user.id,
 *   email: user.email,
 *   role: user.role
 * });
 *
 * // Protect routes
 * app.get('/api/profile', authenticate(auth), (req, res) => {
 *   res.json(req.user);
 * });
 *
 * // Role-based access
 * app.get('/api/admin', authenticate(auth), requireRole('admin'), (req, res) => {
 *   res.json({ admin: true });
 * });
 *
 * // Optional auth (public with user context)
 * app.get('/api/posts', authenticate(auth, { required: false }), (req, res) => {
 *   if (req.user) {
 *     // Personalized response
 *   }
 * });
 * ```
 *
 * Dependencies:
 *   npm install jose express @types/express
 */

// Main class
export { JWTAuth } from './middleware';

// Middleware functions
export { authenticate, requireRole } from './middleware';

// Utility functions
export { generateSecureToken, generateApiKey } from './middleware';

// Types
export type {
  JWTConfig,
  JWTPayload,
  VerifiedUser,
  AuthenticatedRequest,
  AuthMiddlewareOptions,
  AuthErrorType,
  TokenOptions,
  TokenPair,
} from './types';

export { AuthError } from './types';
