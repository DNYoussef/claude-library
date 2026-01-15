/**
 * useAsyncState Hook
 *
 * React hook for managing async operations with loading/error states.
 *
 * Features:
 * - Automatic loading state
 * - Error handling
 * - Request cancellation (via AbortController)
 * - Race condition prevention
 * - TypeScript support
 */

import { useState, useCallback, useRef, useEffect } from 'react';

// Types
interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

interface UseAsyncStateOptions<T> {
  /** Initial data value */
  initialData?: T | null;
  /** Run immediately on mount */
  immediate?: boolean;
  /** Reset data on new request */
  resetOnExecute?: boolean;
  /** Callback on success */
  onSuccess?: (data: T) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

interface UseAsyncStateReturn<T, Args extends unknown[]> {
  /** Current data */
  data: T | null;
  /** Loading state */
  loading: boolean;
  /** Error if any */
  error: Error | null;
  /** Execute the async function */
  execute: (...args: Args) => Promise<T | null>;
  /** Reset state to initial */
  reset: () => void;
  /** Set data directly */
  setData: (data: T | null) => void;
}

/**
 * Hook to manage async state with loading and error handling.
 *
 * @example
 * ```tsx
 * const { data, loading, error, execute } = useAsyncState(
 *   async (userId: string) => {
 *     const response = await fetch(`/api/users/${userId}`);
 *     return response.json();
 *   },
 *   { immediate: false }
 * );
 *
 * // Execute with args
 * await execute('user-123');
 *
 * // In render
 * if (loading) return <Spinner />;
 * if (error) return <Error message={error.message} />;
 * return <UserProfile user={data} />;
 * ```
 */
export function useAsyncState<T, Args extends unknown[] = []>(
  asyncFunction: (...args: Args) => Promise<T>,
  options: UseAsyncStateOptions<T> = {},
): UseAsyncStateReturn<T, Args> {
  const {
    initialData = null,
    immediate = false,
    resetOnExecute = false,
    onSuccess,
    onError,
  } = options;

  const [state, setState] = useState<AsyncState<T>>({
    data: initialData,
    loading: immediate,
    error: null,
  });

  // Track current request to prevent race conditions
  const requestIdRef = useRef(0);
  const mountedRef = useRef(true);

  // Track if we've run the immediate execution
  const hasRunRef = useRef(false);

  // Execute the async function
  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      // Increment request ID to track this request
      const currentRequestId = ++requestIdRef.current;

      setState((prev) => ({
        data: resetOnExecute ? null : prev.data,
        loading: true,
        error: null,
      }));

      try {
        const result = await asyncFunction(...args);

        // Only update if this is the latest request and component is mounted
        if (currentRequestId === requestIdRef.current && mountedRef.current) {
          setState({
            data: result,
            loading: false,
            error: null,
          });
          onSuccess?.(result);
        }

        return result;
      } catch (error) {
        const errorObj = error instanceof Error ? error : new Error(String(error));

        // Only update if this is the latest request and component is mounted
        if (currentRequestId === requestIdRef.current && mountedRef.current) {
          setState((prev) => ({
            data: prev.data,
            loading: false,
            error: errorObj,
          }));
          onError?.(errorObj);
        }

        return null;
      }
    },
    [asyncFunction, resetOnExecute, onSuccess, onError],
  );

  // Reset state
  const reset = useCallback(() => {
    requestIdRef.current++;
    setState({
      data: initialData,
      loading: false,
      error: null,
    });
  }, [initialData]);

  // Set data directly
  const setData = useCallback((data: T | null) => {
    setState((prev) => ({
      ...prev,
      data,
    }));
  }, []);

  // Run immediately on mount if specified
  useEffect(() => {
    if (immediate && !hasRunRef.current) {
      hasRunRef.current = true;
      execute(...([] as unknown as Args));
    }
  }, [immediate, execute]);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return {
    data: state.data,
    loading: state.loading,
    error: state.error,
    execute,
    reset,
    setData,
  };
}

/**
 * Hook for async state with AbortController support.
 *
 * @example
 * ```tsx
 * const { data, loading, execute, abort } = useAbortableAsyncState(
 *   async (signal, userId: string) => {
 *     const response = await fetch(`/api/users/${userId}`, { signal });
 *     return response.json();
 *   }
 * );
 *
 * // Execute
 * execute('user-123');
 *
 * // Cancel if needed
 * abort();
 * ```
 */
export function useAbortableAsyncState<T, Args extends unknown[] = []>(
  asyncFunction: (signal: AbortSignal, ...args: Args) => Promise<T>,
  options: UseAsyncStateOptions<T> = {},
) {
  const abortControllerRef = useRef<AbortController | null>(null);

  const wrappedFunction = useCallback(
    async (...args: Args): Promise<T> => {
      // Abort previous request
      abortControllerRef.current?.abort();

      // Create new controller
      abortControllerRef.current = new AbortController();

      return asyncFunction(abortControllerRef.current.signal, ...args);
    },
    [asyncFunction],
  );

  const result = useAsyncState(wrappedFunction, options);

  const abort = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  return {
    ...result,
    abort,
  };
}

export default useAsyncState;
