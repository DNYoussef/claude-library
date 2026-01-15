/**
 * useLocalStorage Hook
 *
 * A SSR-safe localStorage hook with cross-tab synchronization.
 * Handles serialization, error recovery, and real-time sync across browser tabs.
 *
 * @module react-hooks/useLocalStorage
 * @version 1.0.0
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// ============================================================================
// TYPES
// ============================================================================

export interface UseLocalStorageOptions<T> {
  /** Custom serializer function (default: JSON.stringify) */
  serializer?: (value: T) => string;
  /** Custom deserializer function (default: JSON.parse) */
  deserializer?: (value: string) => T;
  /** Sync across browser tabs (default: true) */
  syncTabs?: boolean;
  /** Called when storage errors occur */
  onError?: (error: Error) => void;
}

export type SetValue<T> = (value: T | ((prevValue: T) => T)) => void;

export interface UseLocalStorageReturn<T> {
  /** Current stored value */
  value: T;
  /** Update the stored value */
  setValue: SetValue<T>;
  /** Remove the item from storage */
  remove: () => void;
  /** Check if storage is available */
  isSupported: boolean;
  /** Last error encountered */
  error: Error | null;
}

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Check if localStorage is available (SSR-safe)
 */
function isLocalStorageAvailable(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  try {
    const testKey = '__storage_test__';
    window.localStorage.setItem(testKey, testKey);
    window.localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/**
 * Default serializer
 */
function defaultSerializer<T>(value: T): string {
  return JSON.stringify(value);
}

/**
 * Default deserializer with type safety
 */
function defaultDeserializer<T>(value: string): T {
  return JSON.parse(value) as T;
}

// ============================================================================
// HOOK IMPLEMENTATION
// ============================================================================

/**
 * React hook for localStorage with cross-tab sync and SSR support.
 *
 * @param key - The localStorage key
 * @param initialValue - Default value when key doesn't exist
 * @param options - Configuration options
 * @returns Object with value, setValue, remove, isSupported, and error
 *
 * @example
 * ```tsx
 * // Basic usage
 * const { value, setValue } = useLocalStorage('theme', 'dark');
 *
 * // With options
 * const { value, setValue, remove, error } = useLocalStorage('user', null, {
 *   syncTabs: true,
 *   onError: (err) => console.error('Storage error:', err),
 * });
 *
 * // Update value
 * setValue('light');
 * setValue((prev) => prev === 'dark' ? 'light' : 'dark');
 *
 * // Remove from storage
 * remove();
 * ```
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: UseLocalStorageOptions<T> = {}
): UseLocalStorageReturn<T> {
  const {
    serializer = defaultSerializer,
    deserializer = defaultDeserializer,
    syncTabs = true,
    onError,
  } = options;

  const isSupported = isLocalStorageAvailable();
  const [error, setError] = useState<Error | null>(null);

  // Use ref to track if this is the initial mount
  const isInitialMount = useRef(true);

  // Store serializer/deserializer in refs to avoid re-renders
  const serializerRef = useRef(serializer);
  const deserializerRef = useRef(deserializer);

  useEffect(() => {
    serializerRef.current = serializer;
    deserializerRef.current = deserializer;
  }, [serializer, deserializer]);

  // Read value from localStorage
  const readValue = useCallback((): T => {
    if (!isSupported) {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      if (item === null) {
        return initialValue;
      }
      return deserializerRef.current(item);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      onError?.(error);
      return initialValue;
    }
  }, [key, initialValue, isSupported, onError]);

  // State to store value
  const [storedValue, setStoredValue] = useState<T>(readValue);

  // Set value in localStorage
  const setValue: SetValue<T> = useCallback(
    (value) => {
      if (!isSupported) {
        console.warn(`useLocalStorage: localStorage is not available`);
        return;
      }

      try {
        // Handle function updates
        const newValue = value instanceof Function ? value(storedValue) : value;

        // Serialize and store
        const serialized = serializerRef.current(newValue);
        window.localStorage.setItem(key, serialized);

        // Update state
        setStoredValue(newValue);
        setError(null);

        // Dispatch storage event for same-window listeners
        // (storage event only fires in other windows by default)
        window.dispatchEvent(
          new StorageEvent('storage', {
            key,
            newValue: serialized,
            storageArea: window.localStorage,
          })
        );
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        onError?.(error);
      }
    },
    [key, storedValue, isSupported, onError]
  );

  // Remove item from localStorage
  const remove = useCallback(() => {
    if (!isSupported) {
      return;
    }

    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
      setError(null);

      // Dispatch removal event
      window.dispatchEvent(
        new StorageEvent('storage', {
          key,
          newValue: null,
          storageArea: window.localStorage,
        })
      );
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      onError?.(error);
    }
  }, [key, initialValue, isSupported, onError]);

  // Sync with localStorage on mount
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      setStoredValue(readValue());
    }
  }, [readValue]);

  // Listen for changes from other tabs
  useEffect(() => {
    if (!isSupported || !syncTabs) {
      return;
    }

    const handleStorageChange = (event: StorageEvent) => {
      if (event.key !== key || event.storageArea !== window.localStorage) {
        return;
      }

      try {
        if (event.newValue === null) {
          setStoredValue(initialValue);
        } else {
          setStoredValue(deserializerRef.current(event.newValue));
        }
        setError(null);
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        onError?.(error);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, initialValue, isSupported, syncTabs, onError]);

  return {
    value: storedValue,
    setValue,
    remove,
    isSupported,
    error,
  };
}

// ============================================================================
// CONVENIENCE EXPORT
// ============================================================================

export default useLocalStorage;
