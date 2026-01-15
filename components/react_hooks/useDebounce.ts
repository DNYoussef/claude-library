/**
 * useDebounce Hook
 *
 * Debounces a value, delaying updates until after a specified delay.
 * Useful for search inputs, form validation, API calls, etc.
 *
 * @module react-hooks/useDebounce
 * @version 1.0.0
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// ============================================================================
// TYPES
// ============================================================================

export interface UseDebounceOptions {
  /** Debounce delay in milliseconds (default: 500) */
  delay?: number;
  /** Leading edge trigger (default: false) */
  leading?: boolean;
  /** Trailing edge trigger (default: true) */
  trailing?: boolean;
  /** Maximum time to wait before forced update (default: undefined) */
  maxWait?: number;
}

export interface UseDebounceReturn<T> {
  /** The debounced value */
  debouncedValue: T;
  /** True when waiting for debounce to settle */
  isPending: boolean;
  /** Cancel pending debounce */
  cancel: () => void;
  /** Flush debounce immediately */
  flush: () => void;
}

export interface UseDebouncedCallbackReturn<T extends (...args: unknown[]) => unknown> {
  /** The debounced callback function */
  debouncedCallback: T;
  /** True when waiting for debounce to settle */
  isPending: boolean;
  /** Cancel pending debounce */
  cancel: () => void;
  /** Flush debounce immediately */
  flush: () => void;
}

// ============================================================================
// VALUE DEBOUNCE HOOK
// ============================================================================

/**
 * React hook to debounce a value.
 *
 * @param value - The value to debounce
 * @param options - Configuration options
 * @returns Object with debouncedValue and control functions
 *
 * @example
 * ```tsx
 * // Basic usage - debounce search input
 * const [searchTerm, setSearchTerm] = useState('');
 * const { debouncedValue } = useDebounce(searchTerm, { delay: 300 });
 *
 * useEffect(() => {
 *   if (debouncedValue) {
 *     searchApi(debouncedValue);
 *   }
 * }, [debouncedValue]);
 *
 * // With pending state
 * const { debouncedValue, isPending } = useDebounce(inputValue, { delay: 500 });
 *
 * return (
 *   <div>
 *     <input value={inputValue} onChange={(e) => setInputValue(e.target.value)} />
 *     {isPending && <Spinner />}
 *   </div>
 * );
 *
 * // With maxWait
 * const { debouncedValue, flush, cancel } = useDebounce(value, {
 *   delay: 1000,
 *   maxWait: 5000, // Force update after 5 seconds
 * });
 * ```
 */
export function useDebounce<T>(
  value: T,
  options: UseDebounceOptions = {}
): UseDebounceReturn<T> {
  const {
    delay = 500,
    leading = false,
    trailing = true,
    maxWait,
  } = options;

  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const [isPending, setIsPending] = useState(false);

  // Refs for tracking timeouts and state
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const maxTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastValueRef = useRef<T>(value);
  const hasLeadingFiredRef = useRef(false);

  // Clear all timeouts
  const clearTimeouts = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (maxTimeoutRef.current) {
      clearTimeout(maxTimeoutRef.current);
      maxTimeoutRef.current = null;
    }
  }, []);

  // Flush: immediately apply the pending value
  const flush = useCallback(() => {
    clearTimeouts();
    setDebouncedValue(lastValueRef.current);
    setIsPending(false);
    hasLeadingFiredRef.current = false;
  }, [clearTimeouts]);

  // Cancel: discard the pending value
  const cancel = useCallback(() => {
    clearTimeouts();
    setIsPending(false);
    hasLeadingFiredRef.current = false;
  }, [clearTimeouts]);

  useEffect(() => {
    lastValueRef.current = value;

    // Handle leading edge
    if (leading && !hasLeadingFiredRef.current) {
      hasLeadingFiredRef.current = true;
      setDebouncedValue(value);

      if (!trailing) {
        return;
      }
    }

    setIsPending(true);

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set trailing edge timeout
    if (trailing) {
      timeoutRef.current = setTimeout(() => {
        setDebouncedValue(value);
        setIsPending(false);
        hasLeadingFiredRef.current = false;

        // Clear maxWait timeout
        if (maxTimeoutRef.current) {
          clearTimeout(maxTimeoutRef.current);
          maxTimeoutRef.current = null;
        }
      }, delay);
    }

    // Set maxWait timeout if specified
    if (maxWait !== undefined && !maxTimeoutRef.current) {
      maxTimeoutRef.current = setTimeout(() => {
        clearTimeouts();
        setDebouncedValue(lastValueRef.current);
        setIsPending(false);
        hasLeadingFiredRef.current = false;
      }, maxWait);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, delay, leading, trailing, maxWait, clearTimeouts]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimeouts();
    };
  }, [clearTimeouts]);

  return {
    debouncedValue,
    isPending,
    cancel,
    flush,
  };
}

// ============================================================================
// CALLBACK DEBOUNCE HOOK
// ============================================================================

/**
 * React hook to debounce a callback function.
 *
 * @param callback - The callback to debounce
 * @param options - Configuration options
 * @returns Object with debouncedCallback and control functions
 *
 * @example
 * ```tsx
 * // Debounce API call
 * const handleSearch = useCallback((query: string) => {
 *   searchApi(query);
 * }, []);
 *
 * const { debouncedCallback } = useDebouncedCallback(handleSearch, { delay: 300 });
 *
 * return (
 *   <input onChange={(e) => debouncedCallback(e.target.value)} />
 * );
 *
 * // With flush on blur
 * const { debouncedCallback, flush } = useDebouncedCallback(saveForm, { delay: 1000 });
 *
 * return (
 *   <textarea
 *     onChange={(e) => debouncedCallback(e.target.value)}
 *     onBlur={flush}
 *   />
 * );
 * ```
 */
export function useDebouncedCallback<T extends (...args: unknown[]) => unknown>(
  callback: T,
  options: UseDebounceOptions = {}
): UseDebouncedCallbackReturn<T> {
  const {
    delay = 500,
    leading = false,
    trailing = true,
    maxWait,
  } = options;

  const [isPending, setIsPending] = useState(false);

  // Refs
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const maxTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const callbackRef = useRef(callback);
  const lastArgsRef = useRef<Parameters<T> | null>(null);
  const hasLeadingFiredRef = useRef(false);

  // Update callback ref
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  // Clear timeouts
  const clearTimeouts = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (maxTimeoutRef.current) {
      clearTimeout(maxTimeoutRef.current);
      maxTimeoutRef.current = null;
    }
  }, []);

  // Execute the callback
  const executeCallback = useCallback(() => {
    if (lastArgsRef.current) {
      callbackRef.current(...lastArgsRef.current);
    }
  }, []);

  // Flush
  const flush = useCallback(() => {
    clearTimeouts();
    executeCallback();
    setIsPending(false);
    hasLeadingFiredRef.current = false;
    lastArgsRef.current = null;
  }, [clearTimeouts, executeCallback]);

  // Cancel
  const cancel = useCallback(() => {
    clearTimeouts();
    setIsPending(false);
    hasLeadingFiredRef.current = false;
    lastArgsRef.current = null;
  }, [clearTimeouts]);

  // Debounced callback
  const debouncedCallback = useCallback(
    ((...args: Parameters<T>) => {
      lastArgsRef.current = args;

      // Handle leading edge
      if (leading && !hasLeadingFiredRef.current) {
        hasLeadingFiredRef.current = true;
        callbackRef.current(...args);

        if (!trailing) {
          return;
        }
      }

      setIsPending(true);

      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set trailing edge timeout
      if (trailing) {
        timeoutRef.current = setTimeout(() => {
          executeCallback();
          setIsPending(false);
          hasLeadingFiredRef.current = false;
          lastArgsRef.current = null;

          if (maxTimeoutRef.current) {
            clearTimeout(maxTimeoutRef.current);
            maxTimeoutRef.current = null;
          }
        }, delay);
      }

      // Set maxWait timeout
      if (maxWait !== undefined && !maxTimeoutRef.current) {
        maxTimeoutRef.current = setTimeout(() => {
          clearTimeouts();
          executeCallback();
          setIsPending(false);
          hasLeadingFiredRef.current = false;
          lastArgsRef.current = null;
        }, maxWait);
      }
    }) as T,
    [delay, leading, trailing, maxWait, clearTimeouts, executeCallback]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimeouts();
    };
  }, [clearTimeouts]);

  return {
    debouncedCallback,
    isPending,
    cancel,
    flush,
  };
}

// ============================================================================
// CONVENIENCE EXPORTS
// ============================================================================

export default useDebounce;
