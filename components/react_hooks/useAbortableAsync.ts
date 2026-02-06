/**
 * useAbortableAsync Hook
 *
 * Manages async operations with AbortController support for cancellation.
 * Automatically aborts pending requests on unmount or new request.
 *
 * @module react-hooks/useAbortableAsync
 * @version 1.0.0
 */

import { useState, useCallback, useRef, useEffect } from 'react';

// ============================================================================
// TYPES
// ============================================================================

export type AbortableStatus = 'idle' | 'loading' | 'success' | 'error' | 'aborted';

export interface AbortableAsyncState<T, E = Error> {
  /** Current data (null if not yet loaded) */
  data: T | null;
  /** Current error (null if no error) */
  error: E | null;
  /** Current status */
  status: AbortableStatus;
  /** True when status is 'loading' */
  isLoading: boolean;
  /** True when status is 'success' */
  isSuccess: boolean;
  /** True when status is 'error' */
  isError: boolean;
  /** True when status is 'aborted' */
  isAborted: boolean;
}

export interface UseAbortableAsyncOptions<T, E = Error> {
  /** Initial data value */
  initialData?: T | null;
  /** Called on successful completion */
  onSuccess?: (data: T) => void;
  /** Called on error */
  onError?: (error: E) => void;
  /** Called when request is aborted */
  onAbort?: () => void;
  /** Abort previous request when new one starts (default: true) */
  abortOnNewRequest?: boolean;
  /** Abort on unmount (default: true) */
  abortOnUnmount?: boolean;
}

export type AbortableAsyncFn<T> = (signal: AbortSignal) => Promise<T>;

export interface UseAbortableAsyncReturn<T, E = Error> extends AbortableAsyncState<T, E> {
  /** Execute an abortable async function */
  execute: <R extends T>(asyncFn: AbortableAsyncFn<R>) => Promise<R | null>;
  /** Abort the current request */
  abort: () => void;
  /** Reset to initial state */
  reset: () => void;
  /** Manually set data */
  setData: (data: T | null) => void;
}

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Check if an error is an AbortError
 */
function isAbortError(error: unknown): boolean {
  return (
    error instanceof DOMException && error.name === 'AbortError' ||
    error instanceof Error && error.name === 'AbortError'
  );
}

// ============================================================================
// HOOK IMPLEMENTATION
// ============================================================================

/**
 * React hook for abortable async operations with automatic cleanup.
 *
 * @param options - Configuration options
 * @returns Object with state values and control functions
 *
 * @example
 * ```tsx
 * // Basic fetch with abort
 * const { data, isLoading, execute, abort } = useAbortableAsync<User[]>();
 *
 * const loadUsers = useCallback(() => {
 *   execute(async (signal) => {
 *     const response = await fetch('/api/users', { signal });
 *     if (!response.ok) throw new Error('Failed to load');
 *     return response.json();
 *   });
 * }, [execute]);
 *
 * // With timeout
 * const { execute } = useAbortableAsync<SearchResults>({
 *   onAbort: () => console.log('Search cancelled'),
 * });
 *
 * const search = async (query: string) => {
 *   const result = await execute(async (signal) => {
 *     // Request will be auto-aborted if user types again
 *     const res = await fetch(`/api/search?q=${query}`, { signal });
 *     return res.json();
 *   });
 * };
 *
 * // Manual abort
 * <button onClick={abort}>Cancel</button>
 * ```
 */
export function useAbortableAsync<T, E = Error>(
  options: UseAbortableAsyncOptions<T, E> = {}
): UseAbortableAsyncReturn<T, E> {
  const {
    initialData = null,
    onSuccess,
    onError,
    onAbort,
    abortOnNewRequest = true,
    abortOnUnmount = true,
  } = options;

  // State
  const [data, setData] = useState<T | null>(initialData);
  const [error, setError] = useState<E | null>(null);
  const [status, setStatus] = useState<AbortableStatus>('idle');

  // AbortController reference
  const abortControllerRef = useRef<AbortController | null>(null);

  // Track mounted state
  const isMountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (abortOnUnmount && abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [abortOnUnmount]);

  // Abort current request
  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;

      if (isMountedRef.current) {
        setStatus('aborted');
        onAbort?.();
      }
    }
  }, [onAbort]);

  // Execute abortable async function
  const execute = useCallback(
    async <R extends T>(asyncFn: AbortableAsyncFn<R>): Promise<R | null> => {
      // Abort previous request if configured
      if (abortOnNewRequest && abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new AbortController
      const controller = new AbortController();
      abortControllerRef.current = controller;

      // Set loading state
      if (isMountedRef.current) {
        setStatus('loading');
        setError(null);
      }

      try {
        const result = await asyncFn(controller.signal);

        // Only update if not aborted and still mounted
        if (!controller.signal.aborted && isMountedRef.current) {
          setData(result);
          setError(null);
          setStatus('success');
          onSuccess?.(result);
        }

        return result;
      } catch (err) {
        // Handle abort
        if (isAbortError(err)) {
          if (isMountedRef.current) {
            setStatus('aborted');
            onAbort?.();
          }
          return null;
        }

        // Handle other errors
        if (isMountedRef.current) {
          const typedError = err as E;
          setError(typedError);
          setStatus('error');
          onError?.(typedError);
        }

        return null;
      } finally {
        // Clean up controller reference if it's the same one
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    },
    [abortOnNewRequest, onSuccess, onError, onAbort]
  );

  // Reset to initial state
  const reset = useCallback(() => {
    abort();
    setData(initialData);
    setError(null);
    setStatus('idle');
  }, [abort, initialData]);

  // Safe data setter
  const safeSetData = useCallback((newData: T | null) => {
    if (isMountedRef.current) {
      setData(newData);
    }
  }, []);

  return {
    data,
    error,
    status,
    isLoading: status === 'loading',
    isSuccess: status === 'success',
    isError: status === 'error',
    isAborted: status === 'aborted',
    execute,
    abort,
    reset,
    setData: safeSetData,
  };
}

// ============================================================================
// CONVENIENCE EXPORT
// ============================================================================

/**
 * Backward-compatible alias for older templates that used useAbortableAsyncState.
 */
export function useAbortableAsyncState<T, E = Error>(
  options: UseAbortableAsyncOptions<T, E> = {}
): UseAbortableAsyncReturn<T, E> {
  return useAbortableAsync(options);
}

export default useAbortableAsync;
