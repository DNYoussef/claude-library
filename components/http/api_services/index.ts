/**
 * API Services - Main Entry Point
 *
 * Reusable HTTP API service layer with:
 * - Generic CRUD patterns via BaseResourceService
 * - Injectable API client configuration
 * - Query builder utilities
 * - Domain-specific services for Productivity and QA
 *
 * @example Basic Usage
 * ```typescript
 * import { createApiClient, createProductivityService } from '@library/api-services';
 *
 * const client = createApiClient({
 *   baseUrl: 'https://api.example.com',
 *   getAuthToken: () => localStorage.getItem('token'),
 * });
 *
 * const productivity = createProductivityService(client);
 *
 * // Use services
 * const notes = await productivity.notes.list({ limit: 10 });
 * const note = await productivity.notes.create({ title: 'New Note' });
 * ```
 *
 * @example Custom Resource Service
 * ```typescript
 * import { ApiClient, BaseResourceService, ListResponse } from '@library/api-services';
 *
 * interface User {
 *   id: number;
 *   email: string;
 *   name: string;
 *   created_at: string;
 *   updated_at: string;
 * }
 *
 * class UsersService extends BaseResourceService<User> {
 *   constructor(client: ApiClient) {
 *     super(client, { endpoint: '/api/v1/users' });
 *   }
 *
 *   async getByEmail(email: string): Promise<User | null> {
 *     const result = await this.list({ email });
 *     return result.items[0] ?? null;
 *   }
 * }
 * ```
 */

// ============ BASE EXPORTS ============

// Core client and utilities
export {
  ApiClient,
  BaseResourceService,
  QueryBuilder,
  query,
  createApiClient,
  createAuthenticatedClient,
  createClientFromEnv,
  isApiError,
  isHttpStatus,
  isNotFound,
  isUnauthorized,
  isForbidden,
  isValidationError,
  isTimeout,
  getValidationErrors,
  getFieldError,
} from './base_service';

// ============ TYPE EXPORTS ============

// Core HTTP types
export type {
  HttpMethod,
  RequestConfig,
  QueryParamValue,
  QueryParams,
  ApiClientConfig,
  ApiError,
  ResourceServiceConfig,
} from './types';

// Response types
export type {
  PaginatedResponse,
  ListResponse,
  DeleteResponse,
  SuccessResponse,
  CountResponse,
} from './types';

// Pagination and filtering types
export type {
  PaginationParams,
  SearchParams,
  SortParams,
  DateRangeParams,
  ListParams,
} from './types';

// Entity base types
export type {
  Identifiable,
  Timestamped,
  SoftDeletable,
  BaseEntity,
  CreateRequest,
  UpdateRequest,
} from './types';

// Utility types
// Note: Use TypeScript's built-in Awaited<T> type instead of a custom one
export type {
  AsyncFunction,
  PartialBy,
  RequiredBy,
  KeysOfType,
} from './types';

// ============ PRODUCTIVITY EXPORTS ============

// Productivity types
export type {
  Note,
  NoteListParams,
  CreateNoteRequest,
  UpdateNoteRequest,
  Idea,
  IdeaListParams,
  CreateIdeaRequest,
  UpdateIdeaRequest,
  IdeaStatus,
  IdeaPriority,
  CalendarEvent,
  CalendarEventListParams,
  CreateCalendarEventRequest,
  UpdateCalendarEventRequest,
  GoogleCalendarSyncRequest,
  GoogleCalendarSyncResponse,
} from './types';

// Productivity services
export {
  NotesService,
  IdeasService,
  CalendarService,
  ProductivityService,
  createNotesService,
  createIdeasService,
  createCalendarService,
  createProductivityService,
} from './productivity_service';

// ============ QA EXPORTS ============

// QA types
export type {
  QARunStatus,
  QAStatusResponse,
  QAHistoryItem,
  QAHistoryResponse,
  QARunRequest,
  QARunResponse,
  QAConfig,
  ComplexityAnalysis,
  ValidationIssue,
  ValidationResponse,
  SpecListItem,
  SpecListResponse,
  SpecOrchestrateRequest,
  SpecOrchestrateResponse,
  SpecAssessment,
  RecoveryStatusResponse,
  SubtaskAttempt,
  SubtaskHistory,
  ClassifyErrorResponse,
  RollbackResponse,
  RecoveryHints,
  RecordAttemptRequest,
} from './types';

// QA services
export {
  QAPipelineService,
  SpecPipelineService,
  RecoveryService,
  QAService,
  createQAPipelineService,
  createSpecPipelineService,
  createRecoveryService,
  createQAService,
} from './qa_service';

// ============ CONVENIENCE EXPORTS ============

/**
 * Create a fully configured API client and services
 */
export async function createServices(config: {
  baseUrl: string;
  getAuthToken?: () => string | null | Promise<string | null>;
  timeout?: number;
}): Promise<{
  client: import('./base_service').ApiClient;
  productivity: import('./productivity_service').ProductivityService;
  qa: import('./qa_service').QAService;
}> {
  const [baseServiceModule, productivityModule, qaModule] = await Promise.all([
    import('./base_service'),
    import('./productivity_service'),
    import('./qa_service'),
  ]);

  const client = new baseServiceModule.ApiClient(config);
  return {
    client,
    productivity: new productivityModule.ProductivityService(client),
    qa: new qaModule.QAService(client),
  };
}

/**
 * Create services from environment variable
 */
export function createServicesFromEnv(
  envVar = 'VITE_API_URL',
  fallbackUrl = '',
  tokenKey = 'auth_token'
): {
  client: import('./base_service').ApiClient;
  productivity: import('./productivity_service').ProductivityService;
  qa: import('./qa_service').QAService;
} {
  const baseUrl =
    (typeof import.meta !== 'undefined' && (import.meta as { env?: Record<string, string> }).env?.[envVar]) ||
    (typeof process !== 'undefined' && process.env?.[envVar]) ||
    fallbackUrl;

  if (!baseUrl) {
    throw new Error(`API URL not configured. Set ${envVar} environment variable.`);
  }

  return createServices({
    baseUrl,
    getAuthToken: () => {
      if (typeof localStorage !== 'undefined') {
        return localStorage.getItem(tokenKey);
      }
      return null;
    },
  });
}
