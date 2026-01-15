/**
 * API Services - Shared Type Definitions
 *
 * Reusable interfaces for HTTP API clients with CRUD patterns,
 * pagination, filtering, and response handling.
 */

// ============ CORE HTTP TYPES ============

/**
 * HTTP methods supported by the API client
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

/**
 * Request configuration for API calls
 */
export interface RequestConfig extends Omit<RequestInit, 'method' | 'body'> {
  /** Query parameters to append to URL */
  params?: QueryParams;
  /** Request body (will be JSON stringified) */
  data?: unknown;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Skip authentication header */
  skipAuth?: boolean;
}

/**
 * Query parameter types supported by the query builder
 */
export type QueryParamValue = string | number | boolean | undefined | null;

/**
 * Query parameters object
 */
export type QueryParams = Record<string, QueryParamValue | QueryParamValue[]>;

/**
 * API client configuration
 */
export interface ApiClientConfig {
  /** Base URL for all API requests */
  baseUrl: string;
  /** Default headers to include in all requests */
  defaultHeaders?: Record<string, string>;
  /** Function to retrieve auth token */
  getAuthToken?: () => string | null | Promise<string | null>;
  /** Default timeout in milliseconds */
  timeout?: number;
  /** Request interceptor */
  onRequest?: (config: RequestInit & { url: string }) => RequestInit & { url: string };
  /** Response interceptor */
  onResponse?: <T>(response: T, status: number) => T;
  /** Error interceptor */
  onError?: (error: ApiError) => void;
}

// ============ RESPONSE TYPES ============

/**
 * Standard API error structure
 */
export interface ApiError extends Error {
  /** HTTP status code */
  status: number;
  /** Error code from server */
  code?: string;
  /** Detailed error message */
  detail?: string;
  /** Field-level validation errors */
  errors?: Record<string, string[]>;
  /** Original response body */
  body?: unknown;
}

/**
 * Paginated list response
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * Simple list response (non-paginated)
 */
export interface ListResponse<T> {
  items: T[];
  total: number;
}

/**
 * Standard delete response
 */
export interface DeleteResponse {
  message: string;
  id: number | string;
}

/**
 * Standard success response
 */
export interface SuccessResponse {
  success: boolean;
  message: string;
}

/**
 * Standard count response
 */
export interface CountResponse {
  count: number;
}

// ============ PAGINATION & FILTERING ============

/**
 * Standard pagination parameters
 */
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

/**
 * Standard search parameters
 */
export interface SearchParams {
  search?: string;
  q?: string;
}

/**
 * Standard sort parameters
 */
export interface SortParams {
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

/**
 * Date range filter parameters
 */
export interface DateRangeParams {
  start_date?: string;
  end_date?: string;
  created_after?: string;
  created_before?: string;
  updated_after?: string;
  updated_before?: string;
}

/**
 * Combined filter parameters for list operations
 */
export interface ListParams extends PaginationParams, SearchParams, SortParams {
  [key: string]: QueryParamValue | undefined;
}

// ============ CRUD OPERATION TYPES ============

/**
 * Entity with standard ID field
 */
export interface Identifiable {
  id: number | string;
}

/**
 * Entity with timestamps
 */
export interface Timestamped {
  created_at: string;
  updated_at: string;
}

/**
 * Entity with soft delete
 */
export interface SoftDeletable {
  deleted_at?: string | null;
  is_deleted?: boolean;
}

/**
 * Standard entity with ID and timestamps
 */
export interface BaseEntity extends Identifiable, Timestamped {}

/**
 * Request type for creating an entity (without ID and timestamps)
 */
export type CreateRequest<T extends BaseEntity> = Omit<T, 'id' | 'created_at' | 'updated_at'>;

/**
 * Request type for updating an entity (partial, without ID and timestamps)
 */
export type UpdateRequest<T extends BaseEntity> = Partial<Omit<T, 'id' | 'created_at' | 'updated_at'>>;

// ============ SERVICE CONFIGURATION ============

/**
 * Resource service configuration
 */
export interface ResourceServiceConfig {
  /** Resource endpoint path (e.g., '/api/v1/notes') */
  endpoint: string;
  /** ID field name (default: 'id') */
  idField?: string;
  /** Custom response transformer */
  transformResponse?: <T>(data: unknown) => T;
  /** Custom request transformer */
  transformRequest?: <T>(data: T) => unknown;
}

// ============ PRODUCTIVITY DOMAIN TYPES ============

/**
 * Note entity
 */
export interface Note extends BaseEntity {
  title: string;
  content: string;
  tags: string[];
  project_id?: number | null;
  is_pinned: boolean;
  is_archived: boolean;
}

/**
 * Note list filters
 */
export interface NoteListParams extends PaginationParams, SearchParams {
  tag?: string;
  project_id?: number;
  is_pinned?: boolean;
  is_archived?: boolean;
}

/**
 * Create note request
 */
export interface CreateNoteRequest {
  title: string;
  content?: string;
  tags?: string[];
  project_id?: number | null;
  is_pinned?: boolean;
}

/**
 * Update note request
 */
export interface UpdateNoteRequest {
  title?: string;
  content?: string;
  tags?: string[];
  project_id?: number | null;
  is_pinned?: boolean;
  is_archived?: boolean;
}

/**
 * Idea status enum
 */
export type IdeaStatus = 'raw' | 'refined' | 'actionable' | 'archived' | 'implemented';

/**
 * Idea priority enum
 */
export type IdeaPriority = 'low' | 'medium' | 'high' | 'critical';

/**
 * Idea entity
 */
export interface Idea extends BaseEntity {
  title: string;
  description: string;
  status: IdeaStatus;
  priority: IdeaPriority;
  tags: string[];
  source?: string;
  related_ideas: number[];
}

/**
 * Idea list filters
 */
export interface IdeaListParams extends PaginationParams, SearchParams {
  status?: IdeaStatus;
  priority?: IdeaPriority;
  tag?: string;
  exclude_archived?: boolean;
}

/**
 * Create idea request
 */
export interface CreateIdeaRequest {
  title: string;
  description?: string;
  status?: IdeaStatus;
  priority?: IdeaPriority;
  tags?: string[];
  source?: string;
}

/**
 * Update idea request
 */
export interface UpdateIdeaRequest {
  title?: string;
  description?: string;
  status?: IdeaStatus;
  priority?: IdeaPriority;
  tags?: string[];
  source?: string;
  related_ideas?: number[];
}

/**
 * Calendar event entity
 */
export interface CalendarEvent extends BaseEntity {
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  all_day: boolean;
  location?: string;
  project_id?: number | null;
  google_event_id?: string | null;
  recurrence_rule?: string | null;
}

/**
 * Calendar event list filters
 */
export interface CalendarEventListParams {
  start_date?: string;
  end_date?: string;
  project_id?: number;
}

/**
 * Create calendar event request
 */
export interface CreateCalendarEventRequest {
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  all_day?: boolean;
  location?: string;
  project_id?: number | null;
}

/**
 * Update calendar event request
 */
export interface UpdateCalendarEventRequest {
  title?: string;
  description?: string;
  start_time?: string;
  end_time?: string;
  all_day?: boolean;
  location?: string;
  project_id?: number | null;
}

/**
 * Google Calendar sync response
 */
export interface GoogleCalendarSyncResponse {
  status: string;
  synced_count: number;
  created_count: number;
  updated_count: number;
  message: string;
}

/**
 * Google Calendar sync request
 */
export interface GoogleCalendarSyncRequest {
  calendar_id?: string;
  days_ahead?: number;
}

// ============ QA DOMAIN TYPES ============

/**
 * QA run status
 */
export type QARunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

/**
 * QA status response
 */
export interface QAStatusResponse {
  spec_dir: string;
  status: QARunStatus;
  last_run?: string;
  pass_rate?: number;
  total_tests?: number;
  passed_tests?: number;
  failed_tests?: number;
  coverage?: number;
}

/**
 * QA history item
 */
export interface QAHistoryItem {
  run_id: string;
  status: QARunStatus;
  started_at: string;
  completed_at?: string;
  pass_rate?: number;
  duration_seconds?: number;
}

/**
 * QA history response
 */
export interface QAHistoryResponse {
  spec_dir: string;
  history: QAHistoryItem[];
  total: number;
}

/**
 * QA run request
 */
export interface QARunRequest {
  spec_dir: string;
  project_dir?: string;
  test_filter?: string;
  parallel?: boolean;
  coverage?: boolean;
}

/**
 * QA run response
 */
export interface QARunResponse {
  run_id: string;
  status: QARunStatus;
  spec_dir: string;
  started_at: string;
  completed_at?: string;
  pass_rate?: number;
  total_tests?: number;
  passed_tests?: number;
  failed_tests?: number;
  coverage?: number;
  error?: string;
}

/**
 * QA configuration
 */
export interface QAConfig {
  default_timeout: number;
  parallel_workers: number;
  coverage_threshold: number;
  retry_failed: boolean;
  retry_count: number;
}

/**
 * Complexity analysis result
 */
export interface ComplexityAnalysis {
  spec_dir: string;
  complexity: 'simple' | 'standard' | 'complex';
  score: number;
  factors: Record<string, number>;
  recommendations: string[];
}

/**
 * Validation issue
 */
export interface ValidationIssue {
  path: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
  line?: number;
  column?: number;
}

/**
 * Validation response
 */
export interface ValidationResponse {
  spec_dir: string;
  valid: boolean;
  issues: ValidationIssue[];
  auto_fixed?: number;
}

/**
 * Spec list item
 */
export interface SpecListItem {
  name: string;
  path: string;
  status: 'active' | 'completed' | 'archived';
  last_modified: string;
}

/**
 * Spec list response
 */
export interface SpecListResponse {
  project_dir: string;
  specs: SpecListItem[];
  total: number;
}

/**
 * Spec orchestrate request
 */
export interface SpecOrchestrateRequest {
  project_dir: string;
  spec_dir: string;
  model?: string;
  skip_phases?: string[];
  force_complexity?: 'simple' | 'standard' | 'complex';
  background?: boolean;
}

/**
 * Spec orchestrate response
 */
export interface SpecOrchestrateResponse {
  run_id: string;
  status: 'started' | 'completed' | 'error';
  message: string;
  spec_dir: string;
  complexity?: string;
  phases?: string[];
  background: boolean;
  started_at: string;
}

/**
 * Spec assessment
 */
export interface SpecAssessment {
  spec_dir: string;
  complexity: ComplexityAnalysis | null;
  validation: ValidationResponse | null;
  qa_status: QAStatusResponse | null;
  recovery_status: RecoveryStatusResponse | null;
  overall_health: 'healthy' | 'warning' | 'critical' | 'unknown';
  recommendations: string[];
  timestamp: string;
}

/**
 * Recovery status response
 */
export interface RecoveryStatusResponse {
  spec_dir: string;
  has_recovery_state: boolean;
  stuck_subtasks: number;
  last_good_commit?: string;
  recovery_available: boolean;
  last_attempt?: string;
}

/**
 * Subtask attempt
 */
export interface SubtaskAttempt {
  session: number;
  success: boolean;
  approach: string;
  error?: string;
  duration_seconds?: number;
  timestamp: string;
}

/**
 * Subtask history
 */
export interface SubtaskHistory {
  subtask_id: string;
  attempts: SubtaskAttempt[];
  total_attempts: number;
  successful_attempts: number;
  last_attempt?: SubtaskAttempt;
}

/**
 * Error classification
 */
export interface ClassifyErrorResponse {
  error_message: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  recoverable: boolean;
  suggested_actions: string[];
  similar_errors?: string[];
}

/**
 * Rollback response
 */
export interface RollbackResponse {
  success: boolean;
  message: string;
  rolled_back_to?: string;
  files_restored?: number;
}

/**
 * Recovery hints
 */
export interface RecoveryHints {
  subtask_id: string;
  hints: string[];
  previous_approaches: string[];
  success_rate: number;
  recommended_approach?: string;
}

/**
 * Record attempt request
 */
export interface RecordAttemptRequest {
  spec_dir: string;
  subtask_id: string;
  session: number;
  success: boolean;
  approach: string;
  error?: string;
  duration_seconds?: number;
  project_dir?: string;
}

// ============ UTILITY TYPES ============

/**
 * Async function type
 */
export type AsyncFunction<TArgs extends unknown[], TResult> = (...args: TArgs) => Promise<TResult>;

// Note: Use TypeScript's built-in Awaited<T> type (available since TS 4.5)
// instead of redefining it here. The built-in handles nested promises correctly.

/**
 * Make specific keys optional
 */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/**
 * Make specific keys required
 */
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>;

/**
 * Extract keys of type from object
 */
export type KeysOfType<T, V> = { [K in keyof T]: T[K] extends V ? K : never }[keyof T];
