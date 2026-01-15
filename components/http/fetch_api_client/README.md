# Fetch API Client

A generalized TypeScript HTTP client built on the Fetch API with support for:

- Configurable base URL
- Request/response interceptors
- Error interceptors
- Timeout configuration
- Retry logic with exponential backoff
- Full TypeScript types

## Origin

Extracted from: `D:\Projects\life-os-frontend\src\services\api.ts`

## Installation

Copy this component to your project:

```bash
cp -r ~/.claude/library/components/http/fetch-api-client ./src/lib/
```

## Quick Start

```typescript
import { createFetchClient, restClient, quickClient } from './fetch-api-client';

// Option 1: Quick client (minimal config)
const api = quickClient('https://api.example.com');

// Option 2: REST client with auth
const authenticatedApi = restClient('https://api.example.com', 'your-bearer-token');

// Option 3: Full configuration
const customApi = createFetchClient({
  baseUrl: 'https://api.example.com',
  defaultHeaders: {
    'X-Custom-Header': 'value',
  },
  timeout: 15000,
  retry: {
    maxRetries: 5,
    baseDelay: 500,
    maxDelay: 10000,
    retryableStatuses: [429, 503],
    retryOnNetworkError: true,
  },
});
```

## Usage

### Basic HTTP Methods

```typescript
import { createFetchClient } from './fetch-api-client';

const api = createFetchClient({ baseUrl: 'https://api.example.com' });

// GET request
const users = await api.get<User[]>('/users');

// POST request
const newUser = await api.post<User>('/users', { name: 'John', email: 'john@example.com' });

// PUT request
const updated = await api.put<User>('/users/123', { name: 'John Updated' });

// PATCH request
const patched = await api.patch<User>('/users/123', { email: 'new@example.com' });

// DELETE request
await api.delete('/users/123');
```

### Request with Custom Options

```typescript
// Full control with request()
const response = await api.request<User>('/users/123', {
  method: 'GET',
  headers: {
    'X-Request-ID': 'abc123',
  },
});
```

### Interceptors

#### Request Interceptor

```typescript
// Add authentication token
const unsubscribe = api.addRequestInterceptor((context) => {
  const token = getAuthToken();
  if (token) {
    context.options.headers = {
      ...context.options.headers,
      Authorization: `Bearer ${token}`,
    };
  }
  return context;
});

// Later: remove interceptor
unsubscribe();
```

#### Response Interceptor

```typescript
// Log all responses
api.addResponseInterceptor((context) => {
  console.log(`[${context.request.options.method}] ${context.request.endpoint}`, {
    status: context.response.status,
    duration: `${context.duration}ms`,
  });
  return context;
});

// Transform response data
api.addResponseInterceptor((context) => {
  if (context.data && typeof context.data === 'object') {
    context.data = transformDates(context.data);
  }
  return context;
});
```

#### Error Interceptor

```typescript
// Handle 401 errors globally
api.addErrorInterceptor((context) => {
  if (context.error instanceof FetchApiError && context.error.status === 401) {
    // Redirect to login
    window.location.href = '/login';
  }
  return context;
});

// Modify retry behavior
api.addErrorInterceptor((context) => {
  // Don't retry on validation errors
  if (context.error instanceof FetchApiError && context.error.status === 422) {
    context.canRetry = false;
  }
  return context;
});
```

### Error Handling

```typescript
import { FetchApiError } from './fetch-api-client';

try {
  const user = await api.get<User>('/users/999');
} catch (error) {
  if (error instanceof FetchApiError) {
    console.log('Status:', error.status);           // 404
    console.log('Message:', error.message);         // "User not found"
    console.log('Data:', error.data);               // { detail: "User not found" }
    console.log('Is Timeout:', error.isTimeout);    // false
    console.log('Is Network:', error.isNetworkError); // false
    console.log('Is Retryable:', error.isRetryable);  // false
  }
}
```

### Singleton Pattern

```typescript
// app/init.ts
import { initDefaultClient } from './fetch-api-client';

initDefaultClient({
  baseUrl: process.env.API_URL,
  timeout: 30000,
});

// app/services/user.ts
import { getDefaultClient } from './fetch-api-client';

export async function getUsers() {
  return getDefaultClient().get<User[]>('/users');
}
```

### Creating Modified Clients

```typescript
// Base client
const api = createFetchClient({ baseUrl: 'https://api.example.com' });

// Create client with different timeout for slow endpoints
const slowApi = api.withConfig({ timeout: 120000 });

// Create client for different service
const analyticsApi = api.withConfig({ baseUrl: 'https://analytics.example.com' });
```

## Configuration Reference

### FetchClientConfig

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `baseUrl` | `string` | Required | Base URL for all requests |
| `defaultHeaders` | `Record<string, string>` | `{'Content-Type': 'application/json'}` | Headers applied to all requests |
| `timeout` | `number` | `30000` | Request timeout in milliseconds |
| `retry` | `RetryConfig` | See below | Retry configuration |
| `redirect` | `RequestRedirect` | `'follow'` | Redirect handling mode |
| `credentials` | `RequestCredentials` | `'same-origin'` | Credentials mode |

### RetryConfig

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `maxRetries` | `number` | `3` | Maximum retry attempts |
| `baseDelay` | `number` | `1000` | Base delay for exponential backoff (ms) |
| `maxDelay` | `number` | `30000` | Maximum delay cap (ms) |
| `retryableStatuses` | `number[]` | `[408, 429, 500, 502, 503, 504]` | Status codes that trigger retry |
| `retryOnNetworkError` | `boolean` | `true` | Retry on network failures |

## Type Exports

```typescript
// Configuration types
export type FetchClientConfig
export type RetryConfig

// Context types
export type RequestContext
export type ResponseContext
export type ErrorContext

// Interceptor types
export type RequestInterceptor
export type ResponseInterceptor
export type ErrorInterceptor

// Error class
export class FetchApiError

// Main class
export class FetchApiClient

// Factory functions
export function createFetchClient(config: FetchClientConfig): FetchApiClient
export function quickClient(baseUrl: string): FetchApiClient
export function restClient(baseUrl: string, token?: string): FetchApiClient

// Singleton helpers
export function initDefaultClient(config: FetchClientConfig): FetchApiClient
export function getDefaultClient(): FetchApiClient
export function resetDefaultClient(): void
```

## Migration from Original

If migrating from the original Life OS Frontend api.ts:

```typescript
// Before (Life OS specific)
import { getTasks, createTask } from './services/api';
const tasks = await getTasks(1, 20);

// After (generalized)
import { createFetchClient } from './lib/fetch-api-client';
import type { Task, PaginatedResponse } from './types';

const api = createFetchClient({ baseUrl: import.meta.env.VITE_API_URL });

async function getTasks(page = 1, pageSize = 20): Promise<PaginatedResponse<Task>> {
  return api.get(`/api/v1/tasks?page=${page}&page_size=${pageSize}`);
}
```

## License

MIT
