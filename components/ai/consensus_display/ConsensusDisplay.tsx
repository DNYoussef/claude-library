/**
 * Consensus Display Component
 *
 * A React component for running and displaying multi-model AI consensus.
 * Supports configurable API endpoints, custom task types, and multiple
 * model providers.
 *
 * @example
 * ```tsx
 * <ConsensusDisplay
 *   apiBase="https://api.example.com"
 *   onConsensusComplete={(result) => console.log(result)}
 * />
 * ```
 *
 * @remarks
 * **Browser/Node.js Compatibility**: The default `fetchFn` parameter uses the
 * global `fetch` API. In browser environments, this works natively. In Node.js
 * environments (v18+), global fetch is available. For older Node.js versions,
 * you must provide a compatible fetch implementation (e.g., `node-fetch` or
 * `undici`) via the `fetchFn` prop.
 *
 * **CSS Styling**: This component includes inline fallback styles but also
 * supports external CSS via class names. For production use, import the
 * companion `ConsensusDisplay.css` file or provide your own styles targeting
 * the documented class names (see CSS_CLASSES constant).
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  ModelStatus,
  ConsensusResult,
  ConsensusDisplayProps,
  TaskType,
  TaskTypeOption,
  ConsensusColorConfig,
} from './types';
import {
  DEFAULT_CONSENSUS_COLORS,
  MODEL_STATUS_COLORS,
} from './types';

/**
 * Default task type options
 */
const DEFAULT_TASK_TYPES: TaskTypeOption[] = [
  { value: 'general', label: 'General' },
  { value: 'validation', label: 'Validation' },
  { value: 'code_review', label: 'Code Review' },
  { value: 'security_audit', label: 'Security Audit' },
];

/**
 * Inline fallback styles for when external CSS is not loaded.
 * These provide a functional baseline appearance.
 */
const FALLBACK_STYLES: Record<string, React.CSSProperties> = {
  container: {
    fontFamily: 'system-ui, -apple-system, sans-serif',
    padding: '16px',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    backgroundColor: '#fafafa',
  },
  header: {
    marginBottom: '16px',
  },
  headerTitle: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    fontWeight: 600,
  },
  modelStatusRow: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap' as const,
  },
  modelStatusBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 8px',
    fontSize: '12px',
    borderRadius: '4px',
    border: '1px solid',
  },
  modelStatusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  input: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  select: {
    padding: '8px',
    fontSize: '14px',
    borderRadius: '4px',
    border: '1px solid #ccc',
  },
  textarea: {
    padding: '8px',
    fontSize: '14px',
    borderRadius: '4px',
    border: '1px solid #ccc',
    resize: 'vertical' as const,
  },
  button: {
    padding: '10px 16px',
    fontSize: '14px',
    fontWeight: 500,
    color: '#fff',
    backgroundColor: '#0066cc',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  buttonDisabled: {
    backgroundColor: '#999',
    cursor: 'not-allowed',
  },
  errorContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    backgroundColor: '#fee',
    border: '1px solid #fcc',
    borderRadius: '4px',
    marginTop: '8px',
  },
  errorMessage: {
    color: '#c00',
    fontSize: '14px',
  },
  retryButton: {
    padding: '4px 8px',
    fontSize: '12px',
    backgroundColor: '#c00',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  result: {
    marginTop: '16px',
  },
  summary: {
    marginBottom: '12px',
  },
  status: {
    display: 'inline-block',
    padding: '4px 12px',
    fontSize: '12px',
    fontWeight: 600,
    color: '#fff',
    borderRadius: '4px',
    marginBottom: '8px',
  },
  stats: {
    display: 'flex',
    gap: '16px',
    fontSize: '14px',
  },
  modelResponses: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  modelResponse: {
    padding: '12px',
    borderRadius: '4px',
    border: '1px solid #e0e0e0',
    backgroundColor: '#fff',
  },
  modelResponseFailed: {
    borderColor: '#fcc',
    backgroundColor: '#fff5f5',
  },
  modelResponseHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
    fontSize: '14px',
  },
  modelName: {
    fontWeight: 600,
  },
  modelConfidence: {
    color: '#666',
  },
  modelTime: {
    color: '#999',
    fontSize: '12px',
  },
  modelError: {
    color: '#c00',
    fontWeight: 500,
  },
  modelResponseBody: {
    fontSize: '13px',
    lineHeight: 1.4,
  },
  pre: {
    margin: 0,
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
    fontFamily: 'monospace',
    fontSize: '12px',
  },
  errorText: {
    color: '#c00',
  },
  noResponse: {
    color: '#999',
    fontStyle: 'italic',
  },
};

/**
 * Get color for consensus status
 */
export function getConsensusColor(
  status: string,
  colors: ConsensusColorConfig = DEFAULT_CONSENSUS_COLORS
): string {
  return colors[status as keyof ConsensusColorConfig] || colors.insufficient;
}

/**
 * Get color for model availability status
 */
export function getModelStatusColor(available: boolean): string {
  return available ? MODEL_STATUS_COLORS.available : MODEL_STATUS_COLORS.unavailable;
}

/**
 * Format consensus status for display
 */
export function formatConsensusStatus(status: string): string {
  return status.replace(/_/g, ' ').toUpperCase();
}

/**
 * ConsensusDisplay - Multi-model AI consensus component
 *
 * Features:
 * - Configurable API endpoint
 * - Multiple task types
 * - Real-time model status
 * - Detailed per-model results
 * - Error handling with retry
 */
export function ConsensusDisplay({
  apiBase,
  taskTypes = DEFAULT_TASK_TYPES,
  onConsensusComplete,
  onError,
  className = '',
  initialPrompt = '',
  initialTaskType = 'general',
  hideModelStatus = false,
  placeholder = 'Enter prompt for multi-model consensus...',
  textareaRows = 3,
  disabled = false,
  fetchFn = fetch,
  headers = {},
}: ConsensusDisplayProps) {
  const [models, setModels] = useState<ModelStatus[]>([]);
  const [prompt, setPrompt] = useState(initialPrompt);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ConsensusResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [taskType, setTaskType] = useState<TaskType | string>(initialTaskType);

  // [H8] Use ref for headers to prevent infinite loop in useCallback dependency
  // Headers object must be memoized by the parent component or stored in a ref
  // to prevent re-creation on every render which would cause useCallback to
  // create a new function reference, triggering the useEffect infinitely.
  const headersRef = useRef(headers);
  headersRef.current = headers;

  // [H9] Track mounted state and abort controller for cleanup
  const isMountedRef = useRef(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      // Abort any in-flight requests on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  /**
   * Fetch available models from the API
   */
  const fetchModels = useCallback(async () => {
    try {
      const response = await fetchFn(`${apiBase}/api/v1/consensus/models/`, {
        headers: {
          'Content-Type': 'application/json',
          ...headersRef.current,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      // Only update state if component is still mounted
      if (isMountedRef.current) {
        setModels(data.models || []);
      }
    } catch (err) {
      console.error('Error fetching models:', err);
      if (isMountedRef.current && onError && err instanceof Error) {
        onError(err);
      }
    }
  }, [apiBase, fetchFn, onError]);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  /**
   * Run consensus with the current prompt.
   * Includes AbortController for cleanup on unmount or cancellation.
   */
  const runConsensus = async () => {
    if (!prompt.trim() || disabled) return;

    // Abort any existing request before starting a new one
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetchFn(`${apiBase}/api/v1/consensus/run/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headersRef.current,
        },
        body: JSON.stringify({
          prompt: prompt,
          task_type: taskType,
        }),
        signal,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Consensus failed');
      }

      const data: ConsensusResult = await response.json();

      // Only update state if component is still mounted
      if (isMountedRef.current) {
        setResult(data);

        if (onConsensusComplete) {
          onConsensusComplete(data);
        }
      }
    } catch (err) {
      // Ignore abort errors - these are expected during cleanup
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }

      // Only update state if component is still mounted
      if (isMountedRef.current) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);

        if (onError && err instanceof Error) {
          onError(err);
        }
      }
    } finally {
      // Only update state if component is still mounted
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  /**
   * Handle retry after error
   */
  const handleRetry = () => {
    setError(null);
    runConsensus();
  };

  return (
    <div
      className={`consensus-display ${className}`.trim()}
      style={FALLBACK_STYLES.container}
    >
      {/* Header with model status */}
      <div className="consensus-header" style={FALLBACK_STYLES.header}>
        <h3 style={FALLBACK_STYLES.headerTitle}>Multi-Model Consensus</h3>
        {!hideModelStatus && models.length > 0 && (
          <div
            className="model-status-row"
            style={FALLBACK_STYLES.modelStatusRow}
            role="list"
            aria-label="Available AI models"
          >
            {models.map((m) => (
              <span
                key={m.name}
                className="model-status-badge"
                style={{
                  ...FALLBACK_STYLES.modelStatusBadge,
                  borderColor: getModelStatusColor(m.available),
                }}
                role="listitem"
                aria-label={`${m.name}: ${m.available ? 'available' : 'unavailable'}`}
              >
                <span
                  className="model-status-dot"
                  style={{
                    ...FALLBACK_STYLES.modelStatusDot,
                    backgroundColor: getModelStatusColor(m.available),
                  }}
                  aria-hidden="true"
                />
                {m.name}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Input section */}
      <div className="consensus-input" style={FALLBACK_STYLES.input}>
        {/* [M11] Added aria-label for accessibility */}
        <select
          value={taskType}
          onChange={(e) => setTaskType(e.target.value)}
          className="consensus-type-select"
          style={FALLBACK_STYLES.select}
          disabled={disabled || loading}
          aria-label="Select task type for consensus"
        >
          {taskTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        {/* [M11] Added aria-label for accessibility */}
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={placeholder}
          className="consensus-textarea"
          style={FALLBACK_STYLES.textarea}
          rows={textareaRows}
          disabled={disabled || loading}
          aria-label="Enter prompt for multi-model consensus"
        />
        <button
          onClick={runConsensus}
          disabled={loading || !prompt.trim() || disabled}
          className="consensus-run-btn"
          style={{
            ...FALLBACK_STYLES.button,
            ...(loading || !prompt.trim() || disabled
              ? FALLBACK_STYLES.buttonDisabled
              : {}),
          }}
        >
          {loading ? 'Running...' : 'Run Consensus'}
        </button>
      </div>

      {/* Error display with retry */}
      {error && (
        <div
          className="error-with-retry"
          style={FALLBACK_STYLES.errorContainer}
          role="alert"
        >
          <span className="error-message" style={FALLBACK_STYLES.errorMessage}>
            {error}
          </span>
          <button
            className="retry-btn"
            style={FALLBACK_STYLES.retryButton}
            onClick={handleRetry}
            disabled={disabled}
            aria-label="Retry consensus request"
          >
            Retry
          </button>
        </div>
      )}

      {/* Results display */}
      {result && (
        <div
          className="consensus-result"
          style={FALLBACK_STYLES.result}
          role="region"
          aria-label="Consensus results"
        >
          {/* Summary section */}
          <div className="consensus-summary" style={FALLBACK_STYLES.summary}>
            <div
              className="consensus-status"
              style={{
                ...FALLBACK_STYLES.status,
                backgroundColor: getConsensusColor(result.consensus_reached),
              }}
              role="status"
              aria-live="polite"
            >
              {formatConsensusStatus(result.consensus_reached)}
            </div>
            <div className="consensus-stats" style={FALLBACK_STYLES.stats}>
              <span className="consensus-stat">
                <strong>{Math.round(result.consensus_confidence * 100)}%</strong> confidence
              </span>
              <span className="consensus-stat">
                <strong>{result.models_agree}/{result.total_models}</strong> models agree
              </span>
              <span className="consensus-stat">
                <strong>{result.execution_time_ms}ms</strong> total
              </span>
            </div>
          </div>

          {/* Per-model responses */}
          <div
            className="model-responses"
            style={FALLBACK_STYLES.modelResponses}
            role="list"
            aria-label="Individual model responses"
          >
            {Object.entries(result.results).map(([name, res]) => (
              <div
                key={name}
                className={`model-response ${res.success ? 'success' : 'failed'}`}
                style={{
                  ...FALLBACK_STYLES.modelResponse,
                  ...(res.success ? {} : FALLBACK_STYLES.modelResponseFailed),
                }}
                role="listitem"
                aria-label={`Response from ${name}`}
              >
                <div
                  className="model-response-header"
                  style={FALLBACK_STYLES.modelResponseHeader}
                >
                  <span className="model-name" style={FALLBACK_STYLES.modelName}>
                    {name}
                  </span>
                  {res.success ? (
                    <>
                      <span
                        className="model-confidence"
                        style={FALLBACK_STYLES.modelConfidence}
                      >
                        {res.confidence ? `${Math.round(res.confidence * 100)}%` : 'N/A'}
                      </span>
                      <span className="model-time" style={FALLBACK_STYLES.modelTime}>
                        {res.execution_ms}ms
                      </span>
                    </>
                  ) : (
                    <span className="model-error" style={FALLBACK_STYLES.modelError}>
                      Error
                    </span>
                  )}
                </div>
                <div
                  className="model-response-body"
                  style={FALLBACK_STYLES.modelResponseBody}
                >
                  {res.success && res.response_preview ? (
                    <pre style={FALLBACK_STYLES.pre}>{res.response_preview}</pre>
                  ) : res.error ? (
                    <span className="error-text" style={FALLBACK_STYLES.errorText}>
                      {res.error}
                    </span>
                  ) : (
                    <span className="no-response" style={FALLBACK_STYLES.noResponse}>
                      Not available
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ConsensusDisplay;
