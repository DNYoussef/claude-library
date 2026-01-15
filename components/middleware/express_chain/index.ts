/**
 * Express Middleware Chain Component
 *
 * Standard Express.js middleware setup with CORS, Helmet, and rate limiting.
 * TypeScript component with consistent interface patterns.
 *
 * Exports:
 *   Middleware Factories:
 *     - createMiddlewareChain: Create full middleware chain
 *     - createCorsMiddleware: CORS handler
 *     - createRateLimitMiddleware: Rate limiting
 *     - createHelmetMiddleware: Security headers
 *     - createLoggingMiddleware: Request logging
 *     - createRequestIdMiddleware: Request ID injection
 *     - createErrorHandler: Error handling middleware
 *
 *   Utilities:
 *     - getClientIp: Extract client IP
 *     - generateRequestId: Create unique request IDs
 *
 *   Types:
 *     - MiddlewareConfig: Main configuration type
 *     - CorsConfig: CORS options
 *     - RateLimitConfig: Rate limiting options
 *     - HelmetConfig: Security header options
 *     - LoggingConfig: Logging options
 */

export {
  // Main factory
  createMiddlewareChain,
  // Individual middleware factories
  createCorsMiddleware,
  createRateLimitMiddleware,
  createHelmetMiddleware,
  createLoggingMiddleware,
  createRequestIdMiddleware,
  createErrorHandler,
  // Utilities
  getClientIp,
  generateRequestId,
} from './middleware';

export type {
  // Configuration types
  MiddlewareConfig,
  CorsConfig,
  RateLimitConfig,
  HelmetConfig,
  LoggingConfig,
} from './middleware';
