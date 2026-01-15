/**
 * Fetch API Client
 * A generalized HTTP client with interceptors, retry logic, and timeout support.
 *
 * Extracted from: D:\Projects\life-os-frontend\src\services\api.ts
 * Version: 1.0.0
 */

// ============ TYPES ============

export interface FetchClientConfig {
  /** Base URL for all requests */
  baseUrl: string;
  /** Default headers applied to all requests */
  defaultHeaders?: Record<string, string>;
  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;
  /** Retry configuration */
  retry?: RetryConfig;
  /** Redirect handling mode (default: 'follow') */
  redirect?: RequestRedirect;
  /** Credentials mode (default: 'same-origin') */
  credentials?: RequestCredentials;
}

export interface RetryConfig {
  /** Maximum number of retry attempts (default: 3) */
  maxRetries: number;
  /** Base delay in milliseconds for exponential backoff (default: 1000) */
  baseDelay: number;
  /** Maximum delay cap in milliseconds (default: 30000) */
  maxDelay: number;
  /** HTTP status codes that should trigger a retry (default: [408, 429, 500, 502, 503, 504]) */
  retryableStatuses: number[];
  /** Whether to retry on network errors (default: true) */
  retryOnNetworkError: boolean;
}

export interface RequestContext {
  /** Request URL (full URL with base) */
  url: string;
  /** Request endpoint (path only) */
  endpoint: string;
  /** Request options */
  options: RequestInit;
  /** Retry attempt number (0 = first attempt) */
  attempt: number;
  /** Request start timestamp */
  startTime: number;
  /** Custom metadata that can be passed through interceptors */
  metadata?: Record<string, unknown>;
}

export interface ResponseContext<T = unknown> {
  /** Original request context */
  request: RequestContext;
  /** Raw Response object */
  response: Response;
  /** Parsed response data (null for empty responses like 204 No Content) */
  data: T | null;
  /** Response duration in milliseconds */
  duration: number;
}

export interface ErrorContext {
  /** Original request context */
  request: RequestContext;
  /** Error that occurred */
  error: Error;
  /** Raw Response object (if available) */
  response?: Response;
  /** Whether the request can be retried */
  canRetry: boolean;
}

export type RequestInterceptor = (context: RequestContext) => RequestContext | Promise<RequestContext>;
export type ResponseInterceptor<T = unknown> = (context: ResponseContext<T>) => ResponseContext<T> | Promise<ResponseContext<T>>;

/**
 * Type guard to check if a type extends string
 */
type IsStringType<T> = T extends string ? true : false;
export type ErrorInterceptor = (context: ErrorContext) => ErrorContext | Promise<ErrorContext>;

export class FetchApiError extends Error {
  public readonly status?: number;
  public readonly statusText?: string;
  public readonly response?: Response;
  public readonly data?: unknown;
  public readonly isTimeout: boolean;
  public readonly isNetworkError: boolean;
  public readonly isRetryable: boolean;

  constructor(
    message: string,
    options: {
      status?: number;
      statusText?: string;
      response?: Response;
      data?: unknown;
      isTimeout?: boolean;
      isNetworkError?: boolean;
      isRetryable?: boolean;
    } = {}
  ) {
    super(message);
    this.name = 'FetchApiError';
    this.status = options.status;
    this.statusText = options.statusText;
    this.response = options.response;
    this.data = options.data;
    this.isTimeout = options.isTimeout ?? false;
    this.isNetworkError = options.isNetworkError ?? false;
    this.isRetryable = options.isRetryable ?? false;
  }
}

// ============ DEFAULT CONFIGURATION ============

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 30000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
  retryOnNetworkError: true,
};

const DEFAULT_TIMEOUT = 30000;

// ============ FETCH API CLIENT CLASS ============

export class FetchApiClient {
  private readonly config: Required<Omit<FetchClientConfig, 'retry'>> & { retry: RetryConfig };
  private readonly requestInterceptors: Array<RequestInterceptor> = [];
  private readonly responseInterceptors: Array<ResponseInterceptor<unknown>> = [];
  private readonly errorInterceptors: Array<ErrorInterceptor> = [];

  constructor(config: FetchClientConfig) {
    this.config = {
      baseUrl: config.baseUrl.replace(/\/$/, ''), // Remove trailing slash
      defaultHeaders: {
        'Content-Type': 'application/json',
        ...config.defaultHeaders,
      },
      timeout: config.timeout ?? DEFAULT_TIMEOUT,
      retry: { ...DEFAULT_RETRY_CONFIG, ...config.retry },
      redirect: config.redirect ?? 'follow',
      credentials: config.credentials ?? 'same-origin',
    };
  }

  // ============ INTERCEPTOR MANAGEMENT ============

  /**
   * Add a request interceptor
   * @param interceptor Function to transform request context before sending
   * @returns Unsubscribe function to remove the interceptor
   */
  public addRequestInterceptor(interceptor: RequestInterceptor): () => void {
    this.requestInterceptors.push(interceptor);
    return () => {
      const index = this.requestInterceptors.indexOf(interceptor);
      if (index > -1) {
        this.requestInterceptors.splice(index, 1);
      }
    };
  }

  /**
   * Add a response interceptor
   * @param interceptor Function to transform response context after receiving
   * @returns Unsubscribe function to remove the interceptor
   */
  public addResponseInterceptor<T = unknown>(interceptor: ResponseInterceptor<T>): () => void {
    // Store with proper typing - interceptors handle unknown and are cast at call site
    const typedInterceptor = interceptor as ResponseInterceptor<unknown>;
    this.responseInterceptors.push(typedInterceptor);
    return () => {
      const index = this.responseInterceptors.indexOf(typedInterceptor);
      if (index > -1) {
        this.responseInterceptors.splice(index, 1);
      }
    };
  }

  /**
   * Add an error interceptor
   * @param interceptor Function to handle/transform errors
   * @returns Unsubscribe function to remove the interceptor
   */
  public addErrorInterceptor(interceptor: ErrorInterceptor): () => void {
    this.errorInterceptors.push(interceptor);
    return () => {
      const index = this.errorInterceptors.indexOf(interceptor);
      if (index > -1) {
        this.errorInterceptors.splice(index, 1);
      }
    };
  }

  // ============ CORE REQUEST METHOD ============

  /**
   * Execute a fetch request with full interceptor and retry support
   * @returns Promise resolving to T, or T | null if empty response is possible
   */
  public async request<T>(
    endpoint: string,
    options: RequestInit = {},
    metadata?: Record<string, unknown>
  ): Promise<T | null> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const startTime = Date.now();

    let context: RequestContext = {
      url,
      endpoint,
      options: {
        ...options,
        headers: {
          ...this.config.defaultHeaders,
          ...options.headers,
        },
        redirect: this.config.redirect,
        credentials: this.config.credentials,
      },
      attempt: 0,
      startTime,
      metadata,
    };

    // Run request interceptors
    for (const interceptor of this.requestInterceptors) {
      context = await interceptor(context);
    }

    return this.executeWithRetry<T>(context);
  }

  // ============ HTTP METHOD SHORTCUTS ============

  public async get<T>(endpoint: string, metadata?: Record<string, unknown>): Promise<T | null> {
    return this.request<T>(endpoint, { method: 'GET' }, metadata);
  }

  public async post<T>(endpoint: string, body?: unknown, metadata?: Record<string, unknown>): Promise<T | null> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: body !== undefined ? JSON.stringify(body) : undefined,
      },
      metadata
    );
  }

  public async put<T>(endpoint: string, body?: unknown, metadata?: Record<string, unknown>): Promise<T | null> {
    return this.request<T>(
      endpoint,
      {
        method: 'PUT',
        body: body !== undefined ? JSON.stringify(body) : undefined,
      },
      metadata
    );
  }

  public async patch<T>(endpoint: string, body?: unknown, metadata?: Record<string, unknown>): Promise<T | null> {
    return this.request<T>(
      endpoint,
      {
        method: 'PATCH',
        body: body !== undefined ? JSON.stringify(body) : undefined,
      },
      metadata
    );
  }

  public async delete<T>(endpoint: string, metadata?: Record<string, unknown>): Promise<T | null> {
    return this.request<T>(endpoint, { method: 'DELETE' }, metadata);
  }

  // ============ PRIVATE METHODS ============

  private async executeWithRetry<T>(context: RequestContext): Promise<T | null> {
    const { retry } = this.config;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retry.maxRetries; attempt++) {
      context = { ...context, attempt };

      try {
        return await this.executeSingleRequest<T>(context);
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        const canRetry =
          attempt < retry.maxRetries &&
          ((error instanceof FetchApiError && error.isRetryable) ||
            (retry.retryOnNetworkError && this.isNetworkError(error)));

        // Run error interceptors
        let errorContext: ErrorContext = {
          request: context,
          error: lastError,
          response: error instanceof FetchApiError ? error.response : undefined,
          canRetry,
        };

        for (const interceptor of this.errorInterceptors) {
          errorContext = await interceptor(errorContext);
        }

        if (!errorContext.canRetry) {
          throw errorContext.error;
        }

        // Calculate delay with exponential backoff and jitter
        const delay = Math.min(
          retry.baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
          retry.maxDelay
        );

        await this.sleep(delay);
      }
    }

    throw lastError;
  }

  private async executeSingleRequest<T>(context: RequestContext): Promise<T | null> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(context.url, {
        ...context.options,
        signal: controller.signal,
      });

      if (!response.ok) {
        const isRetryable = this.config.retry.retryableStatuses.includes(response.status);
        let errorData: unknown;

        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: 'Unknown error' };
        }

        const errorMessage =
          (errorData as { detail?: string })?.detail ||
          (errorData as { message?: string })?.message ||
          `HTTP ${response.status}: ${response.statusText}`;

        throw new FetchApiError(errorMessage, {
          status: response.status,
          statusText: response.statusText,
          response,
          data: errorData,
          isRetryable,
        });
      }

      // Handle empty responses (204 No Content, etc.)
      const contentLength = response.headers.get('content-length');
      const contentType = response.headers.get('content-type');

      let data: T | null;
      if (response.status === 204 || contentLength === '0') {
        // Return null explicitly for empty responses instead of unsafe cast
        data = null;
      } else if (contentType?.includes('application/json')) {
        data = await response.json();
      } else if (contentType?.includes('text/')) {
        // For text responses, return as string and let TypeScript handle type compatibility
        // If T is not string-compatible, this will cause a compile-time error when used incorrectly
        const textContent = await response.text();
        // Type assertion: caller is responsible for ensuring T is string-compatible
        // when making requests that return text content
        data = textContent as unknown as T;
      } else {
        // Unknown content type - attempt to read as text but warn in development
        const textContent = await response.text();
        if (process.env.NODE_ENV === 'development') {
          console.warn(
            `FetchApiClient: Unexpected content-type "${contentType}" for ${context.url}. ` +
            `Response parsed as text. Ensure type parameter T is compatible.`
          );
        }
        data = textContent as unknown as T;
      }

      // Run response interceptors
      let responseContext: ResponseContext<T> = {
        request: context,
        response,
        data,
        duration: Date.now() - context.startTime,
      };

      for (const interceptor of this.responseInterceptors) {
        responseContext = (await interceptor(responseContext)) as ResponseContext<T>;
      }

      return responseContext.data;
    } catch (error) {
      if (error instanceof FetchApiError) {
        throw error;
      }

      // Handle timeout
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new FetchApiError(`Request timeout after ${this.config.timeout}ms`, {
          isTimeout: true,
          isRetryable: true,
        });
      }

      // Handle network errors
      if (this.isNetworkError(error)) {
        throw new FetchApiError(`Network error: ${(error as Error).message}`, {
          isNetworkError: true,
          isRetryable: this.config.retry.retryOnNetworkError,
        });
      }

      throw error;
    } finally {
      // Always cleanup timeout to prevent memory leaks
      clearTimeout(timeoutId);
    }
  }

  private isNetworkError(error: unknown): boolean {
    return (
      error instanceof TypeError ||
      (error instanceof Error &&
        (error.message.includes('Failed to fetch') ||
          error.message.includes('Network request failed') ||
          error.message.includes('net::ERR_')))
    );
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // ============ UTILITY METHODS ============

  /**
   * Get the current configuration (read-only)
   */
  public getConfig(): Readonly<FetchClientConfig> {
    return { ...this.config };
  }

  /**
   * Create a new client with modified configuration
   */
  public withConfig(configOverrides: Partial<FetchClientConfig>): FetchApiClient {
    return new FetchApiClient({
      ...this.config,
      ...configOverrides,
    });
  }

  /**
   * Get the base URL
   */
  public getBaseUrl(): string {
    return this.config.baseUrl;
  }
}

// ============ FACTORY FUNCTION ============

/**
 * Create a new FetchApiClient instance
 */
export function createFetchClient(config: FetchClientConfig): FetchApiClient {
  return new FetchApiClient(config);
}

// ============ SINGLETON HELPER ============

/**
 * Singleton manager with lazy initialization pattern
 * Encapsulates the mutable state to prevent direct module-level access
 */
class DefaultClientManager {
  private static instance: DefaultClientManager | null = null;
  private client: FetchApiClient | null = null;

  private constructor() {
    // Private constructor to enforce singleton
  }

  public static getInstance(): DefaultClientManager {
    if (!DefaultClientManager.instance) {
      DefaultClientManager.instance = new DefaultClientManager();
    }
    return DefaultClientManager.instance;
  }

  public initialize(config: FetchClientConfig): FetchApiClient {
    this.client = new FetchApiClient(config);
    return this.client;
  }

  public getClient(): FetchApiClient {
    if (!this.client) {
      throw new Error('Default FetchApiClient not initialized. Call initDefaultClient() first.');
    }
    return this.client;
  }

  public reset(): void {
    this.client = null;
  }

  public isInitialized(): boolean {
    return this.client !== null;
  }
}

/**
 * Initialize the default client (call once at app startup)
 */
export function initDefaultClient(config: FetchClientConfig): FetchApiClient {
  return DefaultClientManager.getInstance().initialize(config);
}

/**
 * Get the default client (must call initDefaultClient first)
 */
export function getDefaultClient(): FetchApiClient {
  return DefaultClientManager.getInstance().getClient();
}

/**
 * Reset the default client (useful for testing)
 */
export function resetDefaultClient(): void {
  DefaultClientManager.getInstance().reset();
}

/**
 * Check if the default client has been initialized
 */
export function isDefaultClientInitialized(): boolean {
  return DefaultClientManager.getInstance().isInitialized();
}
