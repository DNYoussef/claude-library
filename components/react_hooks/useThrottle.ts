/**
 * useThrottle Hook
 *
 * Throttles a callback function, limiting execution rate.
 * Useful for scroll handlers, resize events, API rate limiting.
 *
 * @module react-hooks/useThrottle
 * @version 1.0.0
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// ============================================================================
// TYPES
// ============================================================================

export interface UseThrottleOptions {
  /** Throttle interval in milliseconds (default: 200) */
  interval?: number;
  /** Execute on leading edge (default: true) */
  leading?: boolean;
  /** Execute on trailing edge (default: true) */
  trailing?: boolean;
}

export interface UseThrottleReturn<T> {
  /** The throttled value */
  throttledValue: T;
  /** True when throttle is active */
  isThrottled: boolean;
}

export interface UseThrottledCallbackReturn<T extends (...args: unknown[]) => unknown> {
  /** The throttled callback function */
  throttledCallback: T;
  /** True when throttle is active */
  isThrottled: boolean;
  /** Cancel pending trailing call */
  cancel: () => void;
  /** Force execute immediately */
  flush: () => void;
}

// ============================================================================
// VALUE THROTTLE HOOK
// ============================================================================

/**
 * React hook to throttle a value.
 *
 * @param value - The value to throttle
 * @param options - Configuration options
 * @returns Object with throttledValue and isThrottled
 *
 * @example
 * ```tsx
 * // Throttle scroll position
 * const [scrollY, setScrollY] = useState(0);
 * const { throttledValue } = useThrottle(scrollY, { interval: 100 });
 *
 * useEffect(() => {
 *   const handleScroll = () => setScrollY(window.scrollY);
 *   window.addEventListener('scroll', handleScroll);
 *   return () => window.removeEventListener('scroll', handleScroll);
 * }, []);
 *
 * // Use throttledValue for expensive operations
 * useEffect(() => {
 *   updateParallax(throttledValue);
 * }, [throttledValue]);
 * ```
 */
export function useThrottle<T>(
  value: T,
  options: UseThrottleOptions = {}
): UseThrottleReturn<T> {
  const {
    interval = 200,
    leading = true,
    trailing = true,
  } = options;

  const [throttledValue, setThrottledValue] = useState<T>(value);
  const [isThrottled, setIsThrottled] = useState(false);

  // Refs
  const lastValueRef = useRef<T>(value);
  const lastExecutedRef = useRef<number>(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    lastValueRef.current = value;
    const now = Date.now();
    const elapsed = now - lastExecutedRef.current;

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    if (elapsed >= interval) {
      // Enough time has passed, execute immediately if leading is enabled
      if (leading || lastExecutedRef.current !== 0) {
        setThrottledValue(value);
        lastExecutedRef.current = now;
        setIsThrottled(false);
      }
    } else {
      // Within throttle window
      setIsThrottled(true);

      if (trailing) {
        // Schedule trailing edge execution
        const remaining = interval - elapsed;
        timeoutRef.current = setTimeout(() => {
          setThrottledValue(lastValueRef.current);
          lastExecutedRef.current = Date.now();
          setIsThrottled(false);
          timeoutRef.current = null;
        }, remaining);
      }
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, interval, leading, trailing]);

  return {
    throttledValue,
    isThrottled,
  };
}

// ============================================================================
// CALLBACK THROTTLE HOOK
// ============================================================================

/**
 * React hook to throttle a callback function.
 *
 * @param callback - The callback to throttle
 * @param options - Configuration options
 * @returns Object with throttledCallback, isThrottled, cancel, and flush
 *
 * @example
 * ```tsx
 * // Throttle scroll handler
 * const handleScroll = useCallback(() => {
 *   console.log('Scroll position:', window.scrollY);
 *   updateUI();
 * }, []);
 *
 * const { throttledCallback } = useThrottledCallback(handleScroll, {
 *   interval: 100,
 * });
 *
 * useEffect(() => {
 *   window.addEventListener('scroll', throttledCallback);
 *   return () => window.removeEventListener('scroll', throttledCallback);
 * }, [throttledCallback]);
 *
 * // Throttle resize with cancel
 * const { throttledCallback, cancel } = useThrottledCallback(handleResize, {
 *   interval: 150,
 *   trailing: true,
 * });
 *
 * // Cancel pending update on specific condition
 * if (shouldCancel) {
 *   cancel();
 * }
 *
 * // Force immediate execution
 * <button onClick={flush}>Update Now</button>
 * ```
 */
export function useThrottledCallback<T extends (...args: unknown[]) => unknown>(
  callback: T,
  options: UseThrottleOptions = {}
): UseThrottledCallbackReturn<T> {
  const {
    interval = 200,
    leading = true,
    trailing = true,
  } = options;

  const [isThrottled, setIsThrottled] = useState(false);

  // Refs
  const callbackRef = useRef(callback);
  const lastArgsRef = useRef<Parameters<T> | null>(null);
  const lastExecutedRef = useRef<number>(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasTrailingRef = useRef(false);

  // Update callback ref
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  // Clear timeout
  const clearScheduled = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Execute callback
  const executeCallback = useCallback((args: Parameters<T>) => {
    callbackRef.current(...args);
    lastExecutedRef.current = Date.now();
    hasTrailingRef.current = false;
    setIsThrottled(false);
  }, []);

  // Cancel
  const cancel = useCallback(() => {
    clearScheduled();
    hasTrailingRef.current = false;
    lastArgsRef.current = null;
    setIsThrottled(false);
  }, [clearScheduled]);

  // Flush
  const flush = useCallback(() => {
    clearScheduled();
    if (lastArgsRef.current) {
      executeCallback(lastArgsRef.current);
      lastArgsRef.current = null;
    }
  }, [clearScheduled, executeCallback]);

  // Throttled callback
  const throttledCallback = useCallback(
    ((...args: Parameters<T>) => {
      lastArgsRef.current = args;
      const now = Date.now();
      const elapsed = now - lastExecutedRef.current;

      if (elapsed >= interval) {
        // Enough time has passed
        clearScheduled();

        if (leading || lastExecutedRef.current !== 0) {
          executeCallback(args);
        } else {
          // First call with leading disabled, schedule for trailing
          hasTrailingRef.current = true;
          setIsThrottled(true);

          if (trailing) {
            timeoutRef.current = setTimeout(() => {
              if (lastArgsRef.current) {
                executeCallback(lastArgsRef.current);
                lastArgsRef.current = null;
              }
              timeoutRef.current = null;
            }, interval);
          }
        }
      } else {
        // Within throttle window
        setIsThrottled(true);
        hasTrailingRef.current = true;

        if (trailing && !timeoutRef.current) {
          const remaining = interval - elapsed;
          timeoutRef.current = setTimeout(() => {
            if (hasTrailingRef.current && lastArgsRef.current) {
              executeCallback(lastArgsRef.current);
              lastArgsRef.current = null;
            }
            timeoutRef.current = null;
          }, remaining);
        }
      }
    }) as T,
    [interval, leading, trailing, clearScheduled, executeCallback]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearScheduled();
    };
  }, [clearScheduled]);

  return {
    throttledCallback,
    isThrottled,
    cancel,
    flush,
  };
}

// ============================================================================
// CONVENIENCE EXPORTS
// ============================================================================

export default useThrottle;
