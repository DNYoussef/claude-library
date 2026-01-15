/**
 * Fetch API Client
 * Generalized HTTP client with interceptors, retry logic, and timeout support.
 *
 * @module fetch-api-client
 * @version 1.0.0
 */

// ============ MAIN EXPORTS ============

export {
  // Class
  FetchApiClient,

  // Error class
  FetchApiError,

  // Factory functions
  createFetchClient,
  initDefaultClient,
  getDefaultClient,
  resetDefaultClient,

  // Types - Configuration
  type FetchClientConfig,
  type RetryConfig,

  // Types - Context
  type RequestContext,
  type ResponseContext,
  type ErrorContext,

  // Types - Interceptors
  type RequestInterceptor,
  type ResponseInterceptor,
  type ErrorInterceptor,
} from './fetch_api_client';

// ============ RE-EXPORT CONVENIENCE ============

import { createFetchClient, type FetchClientConfig } from './fetch_api_client';

/**
 * Quick-start function for simple use cases
 * @param baseUrl - The base URL for API requests
 * @returns Configured FetchApiClient instance
 */
export function quickClient(baseUrl: string): ReturnType<typeof createFetchClient> {
  return createFetchClient({ baseUrl });
}

/**
 * Create a client with common defaults for REST APIs
 * @param baseUrl - The base URL for API requests
 * @param token - Optional bearer token for authentication
 * @returns Configured FetchApiClient instance
 */
export function restClient(
  baseUrl: string,
  token?: string
): ReturnType<typeof createFetchClient> {
  const config: FetchClientConfig = {
    baseUrl,
    defaultHeaders: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    timeout: 30000,
    retry: {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 30000,
      retryableStatuses: [408, 429, 500, 502, 503, 504],
      retryOnNetworkError: true,
    },
  };

  return createFetchClient(config);
}
