/**
 * React Hooks Library
 *
 * Collection of production-ready React hooks for common patterns.
 * All hooks are SSR-compatible and fully typed with TypeScript.
 *
 * @module react-hooks
 * @version 1.0.0
 */

// STORAGE HOOKS
export {
  useLocalStorage,
  type UseLocalStorageOptions,
  type UseLocalStorageReturn,
  type SetValue,
} from './useLocalStorage';

// ASYNC STATE HOOKS
export {
  useAsyncState,
  type AsyncStatus,
  type AsyncState,
  type UseAsyncStateOptions,
  type UseAsyncStateReturn,
} from './useAsyncState';

export {
  useAbortableAsync,
  useAbortableAsyncState,
  type AbortableStatus,
  type AbortableAsyncState,
  type UseAbortableAsyncOptions,
  type UseAbortableAsyncReturn,
  type AbortableAsyncFn,
} from './useAbortableAsync';

// TIMING HOOKS
export {
  useDebounce,
  useDebouncedCallback,
  type UseDebounceOptions,
  type UseDebounceReturn,
  type UseDebouncedCallbackReturn,
} from './useDebounce';

export {
  useThrottle,
  useThrottledCallback,
  type UseThrottleOptions,
  type UseThrottleReturn,
  type UseThrottledCallbackReturn,
} from './useThrottle';
