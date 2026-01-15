# API Services Library

Reusable HTTP API service layer with generic CRUD patterns, injectable configuration, and domain-specific services.

## Features

- **BaseResourceService**: Abstract base class for REST resources with standard CRUD operations
- **ApiClient**: Configurable HTTP client with auth, interceptors, and error handling
- **QueryBuilder**: Fluent API for building URL query parameters
- **Type-safe**: Full TypeScript support with generics
- **Injectable**: API client can be configured and injected for testing

## Installation

Copy the `api-services` directory to your project's library location.

```bash
cp -r api-services/ your-project/src/lib/
```

## Quick Start

```typescript
import { createServices } from './api-services';

// Create client and services
const { client, productivity, qa } = createServices({
  baseUrl: 'https://api.example.com',
  getAuthToken: () => localStorage.getItem('auth_token'),
});

// Use productivity services
const notes = await productivity.notes.list({ limit: 10 });
const note = await productivity.notes.create({ title: 'New Note', content: 'Hello!' });
await productivity.notes.togglePin(note.id);

// Use QA services
const status = await qa.pipeline.getStatus('specs/feature-x');
const run = await qa.pipeline.runAndWait({ spec_dir: 'specs/feature-x' });
```

## API Client Configuration

```typescript
import { createApiClient } from './api-services';

const client = createApiClient({
  // Required
  baseUrl: 'https://api.example.com',

  // Optional: Auth token provider
  getAuthToken: () => localStorage.getItem('token'),

  // Optional: Default headers
  defaultHeaders: {
    'X-Custom-Header': 'value',
  },

  // Optional: Request timeout (default: 30000ms)
  timeout: 60000,

  // Optional: Request interceptor
  onRequest: (config) => {
    console.log('Request:', config.url);
    return config;
  },

  // Optional: Response interceptor
  onResponse: (data, status) => {
    console.log('Response status:', status);
    return data;
  },

  // Optional: Error interceptor
  onError: (error) => {
    console.error('API Error:', error.status, error.message);
  },
});
```

## Query Builder

```typescript
import { query } from './api-services';

// Build query string
const params = query()
  .add('search', 'hello')
  .add('status', 'active')
  .paginate(10, 0)
  .sort('created_at', 'desc')
  .build();
// => "?search=hello&status=active&limit=10&offset=0&sort_by=created_at&sort_order=desc"

// Skip undefined values automatically
const params2 = query()
  .add('search', undefined)  // Skipped
  .add('status', 'active')
  .build();
// => "?status=active"

// Conditional parameters
const params3 = query()
  .addIf(showArchived, 'include_archived', true)
  .build();
```

## Creating Custom Services

Extend `BaseResourceService` for your own resources:

```typescript
import { ApiClient, BaseResourceService, ListResponse } from './api-services';

// Define your entity type
interface User {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'user';
  created_at: string;
  updated_at: string;
}

// Define list parameters
interface UserListParams {
  search?: string;
  role?: 'admin' | 'user';
  limit?: number;
  offset?: number;
}

// Define create/update request types
interface CreateUserRequest {
  email: string;
  name: string;
  role?: 'admin' | 'user';
}

interface UpdateUserRequest {
  email?: string;
  name?: string;
  role?: 'admin' | 'user';
}

// Create your service
class UsersService extends BaseResourceService<
  User,
  CreateUserRequest,
  UpdateUserRequest,
  UserListParams,
  ListResponse<User>
> {
  constructor(client: ApiClient) {
    super(client, { endpoint: '/api/v1/users' });
  }

  // Add custom methods
  async getByEmail(email: string): Promise<User | null> {
    const result = await this.list({ search: email, limit: 1 });
    return result.items[0] ?? null;
  }

  async getAdmins(): Promise<ListResponse<User>> {
    return this.list({ role: 'admin' });
  }

  async changeRole(id: number, role: 'admin' | 'user'): Promise<User> {
    return this.action<User>(id, 'role', 'PATCH', { role });
  }
}

// Usage
const users = new UsersService(client);
const admins = await users.getAdmins();
const user = await users.create({ email: 'test@example.com', name: 'Test' });
await users.changeRole(user.id, 'admin');
```

## Error Handling

```typescript
import {
  isApiError,
  isNotFound,
  isUnauthorized,
  isValidationError,
  getValidationErrors,
  getFieldError,
} from './api-services';

try {
  await productivity.notes.get(999);
} catch (error) {
  if (isNotFound(error)) {
    console.log('Note not found');
  } else if (isUnauthorized(error)) {
    console.log('Please log in');
  } else if (isValidationError(error)) {
    const errors = getValidationErrors(error);
    console.log('Validation errors:', errors);
    const titleError = getFieldError(error, 'title');
    if (titleError) {
      console.log('Title error:', titleError);
    }
  } else if (isApiError(error)) {
    console.log(`API Error ${error.status}: ${error.message}`);
  }
}
```

## Productivity Services

### Notes

```typescript
// List with filters
const notes = await productivity.notes.list({
  search: 'project',
  tag: 'important',
  is_pinned: true,
  limit: 20,
  offset: 0,
});

// CRUD operations
const note = await productivity.notes.create({ title: 'New Note' });
const updated = await productivity.notes.update(note.id, { content: 'Updated' });
await productivity.notes.delete(note.id);

// Special operations
await productivity.notes.togglePin(note.id);
await productivity.notes.toggleArchive(note.id);

// Convenience methods
const pinned = await productivity.notes.getPinned();
const archived = await productivity.notes.getArchived();
const byTag = await productivity.notes.getByTag('work');
const byProject = await productivity.notes.getByProject(1);
```

### Ideas

```typescript
// Status progression
await productivity.ideas.updateStatus(id, 'refined');
await productivity.ideas.promote(id);  // Auto-advance to next status
await productivity.ideas.archive(id);

// Filter by status/priority
const raw = await productivity.ideas.getRaw();
const actionable = await productivity.ideas.getActionable();
const highPriority = await productivity.ideas.getByPriority('high');
```

### Calendar

```typescript
// Date queries
const today = await productivity.calendar.getToday();
const week = await productivity.calendar.getWeek();
const range = await productivity.calendar.getRange('2024-01-01', '2024-01-31');
const upcoming = await productivity.calendar.getUpcoming(30);

// Quick event creation
await productivity.calendar.createQuick('Meeting', '2024-01-15T10:00:00', 60);
await productivity.calendar.createAllDay('Holiday', '2024-12-25');

// Google Calendar sync
await productivity.calendar.syncGoogle({ days_ahead: 30 });
```

### Dashboard Summary

```typescript
const summary = await productivity.getDashboardSummary();
// => { notes: { pinned: 5, total: 100 }, ideas: { raw: 10, ... }, calendar: { ... } }

const searchResults = await productivity.searchAll('project alpha');
// => { notes: [...], ideas: [...] }
```

## QA Services

### QA Pipeline

```typescript
// Check status
const status = await qa.pipeline.getStatus('specs/feature-x');
const history = await qa.pipeline.getHistory('specs/feature-x');

// Run tests
const run = await qa.pipeline.run({ spec_dir: 'specs/feature-x' });
const result = await qa.pipeline.waitForRun(run.run_id);

// Or run and wait in one call
const result = await qa.pipeline.runAndWait({ spec_dir: 'specs/feature-x' });

// Configuration
const config = await qa.pipeline.getConfig();
await qa.pipeline.updateConfig({ parallel_workers: 4 });
```

### Spec Pipeline

```typescript
// Analysis
const complexity = await qa.spec.analyzeComplexity('specs/feature-x');
const validation = await qa.spec.validate('specs/feature-x', undefined, true); // auto-fix

// Orchestration
const run = await qa.spec.orchestrate({
  project_dir: '/path/to/project',
  spec_dir: 'specs/feature-x',
  background: true,
});
const result = await qa.spec.waitForOrchestration(run.run_id);

// Assessment
const assessment = await qa.spec.getAssessment('specs/feature-x');
const health = assessment.overall_health; // 'healthy' | 'warning' | 'critical' | 'unknown'
```

### Recovery

```typescript
// Check recovery status
const status = await qa.recovery.getStatus('specs/feature-x');
const hasStuck = await qa.recovery.hasStuckSubtasks('specs/feature-x');

// Recovery actions
await qa.recovery.rollback('specs/feature-x');
await qa.recovery.clearStuck('specs/feature-x');
await qa.recovery.reset('specs/feature-x');

// Get recommendations
const action = await qa.recovery.getRecommendedAction('specs/feature-x');
// => 'continue' | 'rollback' | 'reset' | 'manual'

// Error classification
const classification = await qa.recovery.classifyError(
  'Connection timeout',
  'specs/feature-x'
);

// Hints
const hints = await qa.recovery.getHints('subtask-1', 'specs/feature-x');
```

### Full QA Cycle

```typescript
// Run complete QA cycle with auto-recovery
const result = await qa.runFullCycle('specs/feature-x', '/project', {
  autoRecover: true,
  timeout: 300000,
});

if (result.recovered) {
  console.log('Had to recover from failure');
}

// Check overall health
const health = await qa.checkHealth('specs/feature-x');
```

## File Structure

```
api-services/
  index.ts              # Main exports
  types.ts              # Type definitions
  base_service.ts       # ApiClient and BaseResourceService
  productivity_service.ts # Notes, Ideas, Calendar services
  qa_service.ts         # QA, Spec, Recovery services
  README.md             # This file
```

## Exported Items

### Classes
- `ApiClient` - HTTP client with auth and interceptors
- `BaseResourceService` - Abstract CRUD service base class
- `QueryBuilder` - Fluent query parameter builder
- `NotesService` - Notes CRUD + pin/archive
- `IdeasService` - Ideas CRUD + status management
- `CalendarService` - Calendar CRUD + Google sync
- `ProductivityService` - Unified productivity facade
- `QAPipelineService` - QA test runs
- `SpecPipelineService` - Spec validation and orchestration
- `RecoveryService` - Error recovery and rollback
- `QAService` - Unified QA facade

### Functions
- `query()` - Create QueryBuilder instance
- `createApiClient()` - Create API client
- `createAuthenticatedClient()` - Create client with localStorage auth
- `createClientFromEnv()` - Create client from environment variable
- `createNotesService()` - Create Notes service
- `createIdeasService()` - Create Ideas service
- `createCalendarService()` - Create Calendar service
- `createProductivityService()` - Create Productivity service
- `createQAPipelineService()` - Create QA Pipeline service
- `createSpecPipelineService()` - Create Spec Pipeline service
- `createRecoveryService()` - Create Recovery service
- `createQAService()` - Create QA service
- `createServices()` - Create all services
- `createServicesFromEnv()` - Create all services from environment

### Error Utilities
- `isApiError()` - Type guard for API errors
- `isHttpStatus()` - Check specific HTTP status
- `isNotFound()` - Check for 404
- `isUnauthorized()` - Check for 401
- `isForbidden()` - Check for 403
- `isValidationError()` - Check for 422
- `isTimeout()` - Check for timeout
- `getValidationErrors()` - Extract validation errors
- `getFieldError()` - Get first error for field

### Types
See `types.ts` for complete type definitions including:
- HTTP types: `HttpMethod`, `RequestConfig`, `ApiClientConfig`, `ApiError`
- Response types: `PaginatedResponse`, `ListResponse`, `DeleteResponse`
- Filter types: `PaginationParams`, `SearchParams`, `SortParams`, `DateRangeParams`
- Entity types: `BaseEntity`, `Identifiable`, `Timestamped`
- Domain types: `Note`, `Idea`, `CalendarEvent`, `QARunResponse`, etc.
