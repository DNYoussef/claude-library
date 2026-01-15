/**
 * useAsyncState Hook
 *
 * Manages async operation state with loading, error, and data states.
 * Includes race condition prevention via request tracking.
 *
 * @module react-hooks/useAsyncState
 * @version 1.0.0
 */

import { useState, useCallback, useRef, useEffect } from 'react';

// ============================================================================
// TYPES
// ============================================================================

export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T, E = Error> {
  /** Current data (null if not yet loaded) */
  data: T | null;
  /** Current error (null if no error) */
  error: E | null;
  /** Current status */
  status: AsyncStatus;
  /** True when status is 'loading' */
  isLoading: boolean;
  /** True when status is 'success' */
  isSuccess: boolean;
  /** True when status is 'error' */
  isError: boolean;
  /** True when status is 'idle' */
  isIdle: boolean;
}

export interface UseAsyncStateOptions<T, E = Error> {
  /** Initial data value */
  initialData?: T | null;
  /** Transform successful data before storing */
  onSuccess?: (data: T) => void;
  /** Handle errors before storing */
  onError?: (error: E) => void;
  /** Reset error on new request (default: true) */
  resetErrorOnLoad?: boolean;
  /** Reset data on new request (default: false) */
  resetDataOnLoad?: boolean;
}

export interface UseAsyncStateReturn<T, E = Error> extends AsyncState<T, E> {
  /** Execute an async function with automatic state management */
  execute: <R extends T>(asyncFn: () => Promise<R>) => Promise<R | null>;
  /** Manually set data */
  setData: (data: T | null) => void;
  /** Manually set error */
  setError: (error: E | null) => void;
  /** Reset to initial state */
  reset: () => void;
}

// ============================================================================
// HOOK IMPLEMENTATION
// ============================================================================

/**
 * React hook for managing async operation state with race condition prevention.
 *
 * @param options - Configuration options
 * @returns Object with state values and control functions
 *
 * @example
 * ```tsx
 * // Basic usage
 * const { data, isLoading, error, execute } = useAsyncState<User[]>();
 *
 * useEffect(() => {
 *   execute(async () => {
 *     const response = await fetch('/api/users');
 *     return response.json();
 *   });
 * }, [execute]);
 *
 * // With options
 * const { data, execute, reset } = useAsyncState<User>({
 *   initialData: null,
 *   onSuccess: (user) => console.log('Loaded:', user),
 *   onError: (err) => toast.error(err.message),
 * });
 *
 * // Manual control
 * const handleSubmit = async () => {
 *   const result = await execute(async () => {
 *     const res = await api.createUser(formData);
 *     return res;
 *   });
 *   if (result) {
 *     navigate('/users');
 *   }
 * };
 * ```
 */
export function useAsyncState<T, E = Error>(
  options: UseAsyncStateOptions<T, E> = {}
): UseAsyncStateReturn<T, E> {
  const {
    initialData = null,
    onSuccess,
    onError,
    resetErrorOnLoad = true,
    resetDataOnLoad = false,
  } = options;

  // State
  const [data, setData] = useState<T | null>(initialData);
  const [error, setError] = useState<E | null>(null);
  const [status, setStatus] = useState<AsyncStatus>('idle');

  // Track request ID to prevent race conditions
  const requestIdRef = useRef(0);

  // Track mounted state for cleanup
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Execute async function with state management
  const execute = useCallback(
    async <R extends T>(asyncFn: () => Promise<R>): Promise<R | null> => {
      // Increment request ID to track this specific request
      const currentRequestId = ++requestIdRef.current;

      // Set loading state
      setStatus('loading');
      if (resetErrorOnLoad) {
        setError(null);
      }
      if (resetDataOnLoad) {
        setData(null);
      }

      try {
        const result = await asyncFn();

        // Only update state if this is still the latest request and component is mounted
        if (currentRequestId === requestIdRef.current && isMountedRef.current) {
          setData(result);
          setError(null);
          setStatus('success');
          onSuccess?.(result);
        }

        return result;
      } catch (err) {
        // Only update state if this is still the latest request and component is mounted
        if (currentRequestId === requestIdRef.current && isMountedRef.current) {
          const typedError = err as E;
          setError(typedError);
          setStatus('error');
          onError?.(typedError);
        }

        return null;
      }
    },
    [resetErrorOnLoad, resetDataOnLoad, onSuccess, onError]
  );

  // Reset to initial state
  const reset = useCallback(() => {
    requestIdRef.current++;
    setData(initialData);
    setError(null);
    setStatus('idle');
  }, [initialData]);

  // Manual setters with safety checks
  const safeSetData = useCallback((newData: T | null) => {
    if (isMountedRef.current) {
      setData(newData);
      if (newData !== null) {
        setStatus('success');
      }
    }
  }, []);

  const safeSetError = useCallback((newError: E | null) => {
    if (isMountedRef.current) {
      setError(newError);
      if (newError !== null) {
        setStatus('error');
      }
    }
  }, []);

  return {
    data,
    error,
    status,
    isLoading: status === 'loading',
    isSuccess: status === 'success',
    isError: status === 'error',
    isIdle: status === 'idle',
    execute,
    setData: safeSetData,
    setError: safeSetError,
    reset,
  };
}

// ============================================================================
// CONVENIENCE EXPORT
// ============================================================================

export default useAsyncState;
