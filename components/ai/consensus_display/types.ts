/**
 * Consensus Display - TypeScript Type Definitions
 *
 * Reusable types for multi-model AI consensus components.
 * Supports custom model providers and configurable endpoints.
 */

// =============================================================================
// MODEL TYPES
// =============================================================================

/**
 * Result from a single model in the consensus process
 */
export interface ModelResult {
  /** Whether the model successfully responded */
  success: boolean;
  /** Preview of the model's response (may be truncated) */
  response_preview: string | null;
  /** Model's confidence in its response (0-1) */
  confidence: number | null;
  /** Execution time in milliseconds */
  execution_ms: number | null;
  /** Error message if the model failed */
  error: string | null;
}

/**
 * Extended model result with full response
 */
export interface ModelResultFull extends ModelResult {
  /** Full response text (not truncated) */
  response_full?: string;
  /** Token count for the response */
  token_count?: number;
  /** Model-specific metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Status of an available model
 */
export interface ModelStatus {
  /** Display name of the model */
  name: string;
  /** Whether the model is currently available */
  available: boolean;
  /** Model identifier (e.g., "gpt-4", "claude-3-opus") */
  model_id: string;
  /** Provider name (e.g., "openai", "anthropic") */
  provider?: string;
  /** Model capabilities */
  capabilities?: ModelCapabilities;
}

/**
 * Model capabilities for routing decisions
 */
export interface ModelCapabilities {
  /** Supports code analysis */
  code_analysis?: boolean;
  /** Supports image input */
  vision?: boolean;
  /** Maximum context length */
  max_tokens?: number;
  /** Supports function calling */
  function_calling?: boolean;
}

// =============================================================================
// CONSENSUS TYPES
// =============================================================================

/**
 * Consensus status levels
 */
export type ConsensusStatus =
  | 'unanimous'      // All models agree
  | 'majority'       // >66% agree
  | 'weak_majority'  // >50% agree
  | 'none'           // No agreement
  | 'insufficient';  // Not enough models responded

/**
 * Task types for consensus routing
 */
export type TaskType =
  | 'general'
  | 'validation'
  | 'code_review'
  | 'security_audit'
  | 'content_analysis'
  | 'fact_checking';

/**
 * Result of a consensus run
 */
export interface ConsensusResult {
  /** Unique identifier for this consensus */
  consensus_id: string;
  /** Run identifier for tracking */
  run_id: string;
  /** Preview of the original prompt */
  prompt_preview: string;
  /** Consensus status achieved */
  consensus_reached: ConsensusStatus;
  /** Overall confidence score (0-1) */
  consensus_confidence: number;
  /** Number of models that agree with consensus */
  models_agree: number;
  /** Total number of models queried */
  total_models: number;
  /** Total execution time in milliseconds */
  execution_time_ms: number;
  /** Results from each model, keyed by model name */
  results: Record<string, ModelResult>;
}

/**
 * Extended consensus result with additional metadata
 */
export interface ConsensusResultFull extends ConsensusResult {
  /** Full results with complete responses */
  results: Record<string, ModelResultFull>;
  /** Timestamp when consensus was reached */
  timestamp?: string;
  /** Task type used for this consensus */
  task_type?: TaskType;
  /** Synthesized answer from agreeing models */
  synthesized_answer?: string;
}

// =============================================================================
// API TYPES
// =============================================================================

/**
 * Request payload for running consensus
 */
export interface ConsensusRequest {
  /** The prompt to send to all models */
  prompt: string;
  /** Type of task for model routing */
  task_type?: TaskType;
  /** Specific models to include (optional) */
  include_models?: string[];
  /** Specific models to exclude (optional) */
  exclude_models?: string[];
  /** Maximum response time per model in ms */
  timeout_ms?: number;
  /** Minimum confidence threshold */
  min_confidence?: number;
}

/**
 * Response from models endpoint
 */
export interface ModelsResponse {
  /** List of available models */
  models: ModelStatus[];
  /** Timestamp of status check */
  checked_at?: string;
}

/**
 * API error response
 */
export interface ApiError {
  /** Error message */
  detail: string;
  /** Error code (optional) */
  code?: string;
  /** Validation errors (optional) */
  errors?: Record<string, string[]>;
}

// =============================================================================
// COMPONENT PROPS
// =============================================================================

/**
 * Props for the ConsensusDisplay component
 */
export interface ConsensusDisplayProps {
  /** Base URL for the API (e.g., "https://api.example.com") */
  apiBase: string;
  /** Custom task types to display in dropdown */
  taskTypes?: TaskTypeOption[];
  /** Callback when consensus completes */
  onConsensusComplete?: (result: ConsensusResult) => void;
  /** Callback when an error occurs */
  onError?: (error: Error) => void;
  /** Custom class name for styling */
  className?: string;
  /** Initial prompt value */
  initialPrompt?: string;
  /** Initial task type */
  initialTaskType?: TaskType;
  /** Hide the models status row */
  hideModelStatus?: boolean;
  /** Custom placeholder text */
  placeholder?: string;
  /** Number of rows for textarea */
  textareaRows?: number;
  /** Disable the component */
  disabled?: boolean;
  /** Custom fetch function for API calls */
  fetchFn?: typeof fetch;
  /** Custom headers for API calls */
  headers?: Record<string, string>;
}

/**
 * Task type option for dropdown
 */
export interface TaskTypeOption {
  /** Value to send to API */
  value: TaskType | string;
  /** Display label */
  label: string;
}

// =============================================================================
// HOOKS TYPES
// =============================================================================

/**
 * State returned by useConsensus hook
 */
export interface UseConsensusState {
  /** Available models */
  models: ModelStatus[];
  /** Whether models are loading */
  modelsLoading: boolean;
  /** Whether consensus is running */
  consensusLoading: boolean;
  /** Current result */
  result: ConsensusResult | null;
  /** Current error */
  error: string | null;
}

/**
 * Actions returned by useConsensus hook
 */
export interface UseConsensusActions {
  /** Fetch available models */
  fetchModels: () => Promise<void>;
  /** Run consensus with given prompt and task type */
  runConsensus: (prompt: string, taskType?: TaskType) => Promise<ConsensusResult | null>;
  /** Clear current result */
  clearResult: () => void;
  /** Clear current error */
  clearError: () => void;
}

/**
 * Return type of useConsensus hook
 */
export type UseConsensusReturn = UseConsensusState & UseConsensusActions;

// =============================================================================
// UTILITY TYPES
// =============================================================================

/**
 * Color configuration for consensus statuses
 */
export interface ConsensusColorConfig {
  unanimous: string;
  majority: string;
  weak_majority: string;
  none: string;
  insufficient: string;
}

/**
 * Default color configuration
 */
export const DEFAULT_CONSENSUS_COLORS: ConsensusColorConfig = {
  unanimous: '#22c55e',    // Green
  majority: '#84cc16',     // Lime
  weak_majority: '#eab308', // Yellow
  none: '#ef4444',         // Red
  insufficient: '#94a3b8'  // Gray
};

/**
 * Model availability colors
 */
export const MODEL_STATUS_COLORS = {
  available: '#22c55e',    // Green
  unavailable: '#ef4444'   // Red
} as const;
