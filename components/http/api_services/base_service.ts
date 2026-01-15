/**
 * API Services - Abstract Base Service
 *
 * Provides common HTTP client patterns with:
 * - Injectable API client configuration
 * - Query parameter builder utilities
 * - CRUD operation base methods
 * - Error handling and transformation
 * - Request/response interceptors
 */

import type {
  ApiClientConfig,
  ApiError,
  HttpMethod,
  QueryParams,
  QueryParamValue,
  RequestConfig,
  PaginatedResponse,
  ListResponse,
  DeleteResponse,
  SuccessResponse,
  ResourceServiceConfig,
  ListParams,
  Identifiable,
} from './types';

// ============ QUERY BUILDER ============

/**
 * Query parameter builder with fluent API
 */
export class QueryBuilder {
  private params: URLSearchParams;

  constructor(initial?: QueryParams) {
    this.params = new URLSearchParams();
    if (initial) {
      this.addAll(initial);
    }
  }

  /**
   * Add a single parameter (skips undefined/null values)
   */
  add(key: string, value: QueryParamValue): this {
    if (value !== undefined && value !== null && value !== '') {
      this.params.append(key, String(value));
    }
    return this;
  }

  /**
   * Add multiple parameters from object
   */
  addAll(params: QueryParams): this {
    for (const [key, value] of Object.entries(params)) {
      if (Array.isArray(value)) {
        for (const v of value) {
          this.add(key, v);
        }
      } else {
        this.add(key, value);
      }
    }
    return this;
  }

  /**
   * Add parameter only if condition is true
   */
  addIf(condition: boolean, key: string, value: QueryParamValue): this {
    if (condition) {
      this.add(key, value);
    }
    return this;
  }

  /**
   * Add pagination parameters
   */
  paginate(limit?: number, offset?: number): this {
    return this.add('limit', limit).add('offset', offset);
  }

  /**
   * Add search parameter
   */
  search(query?: string, field = 'search'): this {
    return this.add(field, query);
  }

  /**
   * Add sort parameters
   */
  sort(sortBy?: string, order?: 'asc' | 'desc'): this {
    return this.add('sort_by', sortBy).add('sort_order', order);
  }

  /**
   * Add date range parameters
   */
  dateRange(start?: string, end?: string, prefix = ''): this {
    const startKey = prefix ? `${prefix}_start_date` : 'start_date';
    const endKey = prefix ? `${prefix}_end_date` : 'end_date';
    return this.add(startKey, start).add(endKey, end);
  }

  /**
   * Build query string (with leading '?' if not empty)
   */
  build(): string {
    const query = this.params.toString();
    return query ? `?${query}` : '';
  }

  /**
   * Build query string without leading '?'
   */
  toString(): string {
    return this.params.toString();
  }

  /**
   * Check if any parameters are set
   */
  isEmpty(): boolean {
    return this.params.toString() === '';
  }

  /**
   * Get the underlying URLSearchParams
   */
  toURLSearchParams(): URLSearchParams {
    return this.params;
  }
}

/**
 * Create a query builder with initial parameters
 */
export function query(initial?: QueryParams): QueryBuilder {
  return new QueryBuilder(initial);
}

// ============ API CLIENT ============

/**
 * HTTP API client with configurable base URL, auth, and interceptors
 */
export class ApiClient {
  private config: Required<Pick<ApiClientConfig, 'baseUrl' | 'timeout'>> & ApiClientConfig;

  constructor(config: ApiClientConfig) {
    this.config = {
      baseUrl: config.baseUrl.replace(/\/$/, ''), // Remove trailing slash
      timeout: config.timeout ?? 30000,
      defaultHeaders: config.defaultHeaders ?? {},
      ...config,
    };
  }

  /**
   * Get the base URL
   */
  get baseUrl(): string {
    return this.config.baseUrl;
  }

  /**
   * Make an HTTP request
   */
  async request<T>(method: HttpMethod, endpoint: string, config?: RequestConfig): Promise<T> {
    const url = this.buildUrl(endpoint, config?.params);
    const headers = await this.buildHeaders(config);
    const body = config?.data ? JSON.stringify(config.data) : undefined;

    let requestConfig: RequestInit & { url: string } = {
      url,
      method,
      headers,
      body,
      ...config,
    };

    // Apply request interceptor
    if (this.config.onRequest) {
      requestConfig = this.config.onRequest(requestConfig);
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config?.timeout ?? this.config.timeout);

    try {
      const response = await fetch(requestConfig.url, {
        ...requestConfig,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw await this.createError(response);
      }

      // Handle empty responses
      const text = await response.text();
      let data: T = (text ? JSON.parse(text) : {}) as T;

      // Apply response interceptor
      if (this.config.onResponse) {
        data = this.config.onResponse(data, response.status);
      }

      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error && error.name === 'AbortError') {
        const timeoutError = this.createTimeoutError(url);
        if (this.config.onError) {
          this.config.onError(timeoutError);
        }
        throw timeoutError;
      }

      if (this.isApiError(error)) {
        if (this.config.onError) {
          this.config.onError(error);
        }
        throw error;
      }

      const wrappedError = this.wrapError(error);
      if (this.config.onError) {
        this.config.onError(wrappedError);
      }
      throw wrappedError;
    }
  }

  /**
   * GET request
   */
  get<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>('GET', endpoint, config);
  }

  /**
   * POST request
   */
  post<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.request<T>('POST', endpoint, { ...config, data });
  }

  /**
   * PUT request
   */
  put<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.request<T>('PUT', endpoint, { ...config, data });
  }

  /**
   * PATCH request
   */
  patch<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.request<T>('PATCH', endpoint, { ...config, data });
  }

  /**
   * DELETE request
   */
  delete<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>('DELETE', endpoint, config);
  }

  /**
   * Build full URL with query parameters
   */
  private buildUrl(endpoint: string, params?: QueryParams): string {
    const base = endpoint.startsWith('http') ? endpoint : `${this.config.baseUrl}${endpoint}`;
    if (!params) return base;

    const queryString = query(params).build();
    return `${base}${queryString}`;
  }

  /**
   * Build request headers
   */
  private async buildHeaders(config?: RequestConfig): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...this.config.defaultHeaders,
      ...(config?.headers as Record<string, string>),
    };

    // Add auth token if available and not skipped
    if (!config?.skipAuth && this.config.getAuthToken) {
      const token = await this.config.getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  /**
   * Create API error from response
   */
  private async createError(response: Response, originalError?: Error): Promise<ApiError> {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = { detail: response.statusText || 'Unknown error' };
    }

    const error = new Error(
      (body as { detail?: string })?.detail ||
      (body as { message?: string })?.message ||
      `HTTP ${response.status}`
    ) as ApiError;

    error.status = response.status;
    error.code = (body as { code?: string })?.code;
    error.detail = (body as { detail?: string })?.detail;
    error.errors = (body as { errors?: Record<string, string[]> })?.errors;
    error.body = body;

    // Preserve stack trace by setting original error as cause
    if (originalError) {
      error.cause = originalError;
    }

    // Capture stack trace at error creation point
    if (Error.captureStackTrace) {
      Error.captureStackTrace(error, this.createError);
    }

    return error;
  }

  /**
   * Create timeout error
   */
  private createTimeoutError(url: string): ApiError {
    const error = new Error(`Request timeout: ${url}`) as ApiError;
    error.status = 408;
    error.code = 'TIMEOUT';
    return error;
  }

  /**
   * Wrap unknown error as ApiError
   */
  private wrapError(error: unknown): ApiError {
    if (error instanceof Error) {
      const apiError = error as ApiError;
      apiError.status = apiError.status ?? 0;
      return apiError;
    }
    const wrappedError = new Error(String(error)) as ApiError;
    wrappedError.status = 0;
    return wrappedError;
  }

  /**
   * Type guard for ApiError
   */
  private isApiError(error: unknown): error is ApiError {
    return error instanceof Error && 'status' in error;
  }
}

// ============ BASE RESOURCE SERVICE ============

/**
 * Abstract base service for REST resources with standard CRUD operations
 */
export abstract class BaseResourceService<
  TEntity extends Identifiable,
  TCreateRequest = Partial<TEntity>,
  TUpdateRequest = Partial<TEntity>,
  TListParams extends ListParams = ListParams,
  TListResponse = ListResponse<TEntity>
> {
  protected client: ApiClient;
  protected config: ResourceServiceConfig;

  constructor(client: ApiClient, config: ResourceServiceConfig) {
    this.client = client;
    this.config = {
      idField: 'id',
      ...config,
    };
  }

  /**
   * Get the resource endpoint
   */
  protected get endpoint(): string {
    return this.config.endpoint;
  }

  /**
   * Build URL for a specific resource
   */
  protected resourceUrl(id: number | string): string {
    return `${this.endpoint}/${id}`;
  }

  /**
   * Build URL for a sub-resource action
   */
  protected actionUrl(id: number | string, action: string): string {
    return `${this.endpoint}/${id}/${action}`;
  }

  /**
   * Transform request data before sending
   */
  protected transformRequest<T>(data: T): unknown {
    return this.config.transformRequest ? this.config.transformRequest(data) : data;
  }

  /**
   * Transform response data after receiving
   */
  protected transformResponse<T>(data: unknown): T {
    return this.config.transformResponse ? this.config.transformResponse(data) : data as T;
  }

  /**
   * Build query parameters for list operations
   */
  protected buildListParams(params?: TListParams): QueryBuilder {
    if (!params) return query();
    return query(params as QueryParams);
  }

  /**
   * List resources with optional filtering
   */
  async list(params?: TListParams): Promise<TListResponse> {
    const queryString = this.buildListParams(params).build();
    const response = await this.client.get<TListResponse>(`${this.endpoint}${queryString}`);
    return this.transformResponse<TListResponse>(response);
  }

  /**
   * Get a single resource by ID
   */
  async get(id: number | string): Promise<TEntity> {
    const response = await this.client.get<TEntity>(this.resourceUrl(id));
    return this.transformResponse<TEntity>(response);
  }

  /**
   * Create a new resource
   */
  async create(data: TCreateRequest): Promise<TEntity> {
    const response = await this.client.post<TEntity>(
      this.endpoint,
      this.transformRequest(data)
    );
    return this.transformResponse<TEntity>(response);
  }

  /**
   * Update an existing resource
   */
  async update(id: number | string, data: TUpdateRequest): Promise<TEntity> {
    const response = await this.client.put<TEntity>(
      this.resourceUrl(id),
      this.transformRequest(data)
    );
    return this.transformResponse<TEntity>(response);
  }

  /**
   * Partially update a resource
   */
  async patch(id: number | string, data: Partial<TUpdateRequest>): Promise<TEntity> {
    const response = await this.client.patch<TEntity>(
      this.resourceUrl(id),
      this.transformRequest(data)
    );
    return this.transformResponse<TEntity>(response);
  }

  /**
   * Delete a resource
   */
  async delete(id: number | string): Promise<DeleteResponse> {
    return this.client.delete<DeleteResponse>(this.resourceUrl(id));
  }

  /**
   * Check if a resource exists
   */
  async exists(id: number | string): Promise<boolean> {
    try {
      await this.get(id);
      return true;
    } catch (error) {
      if ((error as ApiError).status === 404) {
        return false;
      }
      throw error;
    }
  }

  /**
   * Perform a custom action on a resource
   */
  protected async action<T>(
    id: number | string,
    action: string,
    method: HttpMethod = 'POST',
    data?: unknown
  ): Promise<T> {
    const url = this.actionUrl(id, action);
    switch (method) {
      case 'GET':
        return this.client.get<T>(url);
      case 'POST':
        return this.client.post<T>(url, data);
      case 'PUT':
        return this.client.put<T>(url, data);
      case 'PATCH':
        return this.client.patch<T>(url, data);
      case 'DELETE':
        return this.client.delete<T>(url);
    }
  }

  /**
   * Perform a collection-level action
   */
  protected async collectionAction<T>(
    action: string,
    method: HttpMethod = 'POST',
    data?: unknown,
    params?: QueryParams
  ): Promise<T> {
    const url = `${this.endpoint}/${action}${query(params).build()}`;
    switch (method) {
      case 'GET':
        return this.client.get<T>(url);
      case 'POST':
        return this.client.post<T>(url, data);
      case 'PUT':
        return this.client.put<T>(url, data);
      case 'PATCH':
        return this.client.patch<T>(url, data);
      case 'DELETE':
        return this.client.delete<T>(url);
    }
  }
}

// ============ FACTORY FUNCTIONS ============

/**
 * Create an API client with default configuration
 */
export function createApiClient(config: ApiClientConfig): ApiClient {
  return new ApiClient(config);
}

/**
 * Create an API client with localStorage token auth
 */
export function createAuthenticatedClient(
  baseUrl: string,
  tokenKey = 'auth_token'
): ApiClient {
  return new ApiClient({
    baseUrl,
    getAuthToken: () => localStorage.getItem(tokenKey),
  });
}

/**
 * Create an API client from environment variable
 */
export function createClientFromEnv(
  envVar = 'VITE_API_URL',
  fallbackUrl = '',
  tokenKey = 'auth_token'
): ApiClient {
  let baseUrl = fallbackUrl;

  // Try Vite/ESM import.meta.env (with proper typeof checks)
  try {
    if (typeof import.meta !== 'undefined' && import.meta !== null) {
      const meta = import.meta as { env?: Record<string, string> };
      if (typeof meta.env === 'object' && meta.env !== null && envVar in meta.env) {
        const envValue = meta.env[envVar];
        if (typeof envValue === 'string' && envValue.length > 0) {
          baseUrl = envValue;
        }
      }
    }
  } catch {
    // import.meta not available in this context, continue to fallback
  }

  // Try Node.js process.env
  if (!baseUrl) {
    try {
      if (typeof process !== 'undefined' && process !== null && typeof process.env === 'object' && process.env !== null) {
        const envValue = process.env[envVar];
        if (typeof envValue === 'string' && envValue.length > 0) {
          baseUrl = envValue;
        }
      }
    } catch {
      // process not available in this context
    }
  }

  if (!baseUrl) {
    throw new Error(`API URL not configured. Set ${envVar} environment variable.`);
  }

  return createAuthenticatedClient(baseUrl, tokenKey);
}

// ============ UTILITY FUNCTIONS ============

/**
 * Check if an error is an API error
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof Error && 'status' in error;
}

/**
 * Check if error is a specific HTTP status
 */
export function isHttpStatus(error: unknown, status: number): boolean {
  return isApiError(error) && error.status === status;
}

/**
 * Check if error is a 404 Not Found
 */
export function isNotFound(error: unknown): boolean {
  return isHttpStatus(error, 404);
}

/**
 * Check if error is a 401 Unauthorized
 */
export function isUnauthorized(error: unknown): boolean {
  return isHttpStatus(error, 401);
}

/**
 * Check if error is a 403 Forbidden
 */
export function isForbidden(error: unknown): boolean {
  return isHttpStatus(error, 403);
}

/**
 * Check if error is a 422 Validation Error
 */
export function isValidationError(error: unknown): boolean {
  return isHttpStatus(error, 422);
}

/**
 * Check if error is a timeout
 */
export function isTimeout(error: unknown): boolean {
  return isApiError(error) && error.code === 'TIMEOUT';
}

/**
 * Extract validation errors from API error
 */
export function getValidationErrors(error: unknown): Record<string, string[]> {
  if (isApiError(error) && error.errors) {
    return error.errors;
  }
  return {};
}

/**
 * Get first validation error message for a field
 */
export function getFieldError(error: unknown, field: string): string | undefined {
  const errors = getValidationErrors(error);
  return errors[field]?.[0];
}
