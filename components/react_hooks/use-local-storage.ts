/**
 * useLocalStorage Hook
 *
 * React hook for persisting state to localStorage with sync across tabs.
 * Based on usehooks-ts patterns.
 *
 * References:
 * - https://github.com/juliencrn/usehooks-ts
 * - https://github.com/astoilkov/use-local-storage-state
 *
 * Features:
 * - Cross-tab synchronization
 * - SSR-safe (works with Next.js)
 * - TypeScript support
 * - Automatic JSON serialization
 * - Error handling for quota exceeded
 */

import { useState, useEffect, useCallback, useSyncExternalStore } from 'react';

// Types
type SetValue<T> = T | ((val: T) => T);
type RemoveValue = () => void;

interface UseLocalStorageOptions<T> {
  /** Default value if nothing in storage */
  defaultValue?: T;
  /** Custom serializer (default: JSON.stringify) */
  serializer?: (value: T) => string;
  /** Custom deserializer (default: JSON.parse) */
  deserializer?: (value: string) => T;
  /** Sync value from server (for SSR) */
  initializeWithValue?: boolean;
}

/**
 * Hook to manage localStorage state with React.
 *
 * @example
 * ```tsx
 * const [theme, setTheme, removeTheme] = useLocalStorage('theme', 'light');
 *
 * // Update
 * setTheme('dark');
 *
 * // With function updater
 * setTheme(prev => prev === 'light' ? 'dark' : 'light');
 *
 * // Remove from storage
 * removeTheme();
 * ```
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: UseLocalStorageOptions<T> = {},
): [T, (value: SetValue<T>) => void, RemoveValue] {
  const {
    defaultValue = initialValue,
    serializer = JSON.stringify,
    deserializer = JSON.parse,
    initializeWithValue = true,
  } = options;

  // SSR safety check
  const isClient = typeof window !== 'undefined';

  // Read from localStorage
  const readValue = useCallback((): T => {
    if (!isClient) {
      return defaultValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      if (item === null) {
        return defaultValue;
      }
      // Handle 'undefined' string case
      if (item === 'undefined') {
        return undefined as T;
      }
      return deserializer(item);
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return defaultValue;
    }
  }, [key, defaultValue, deserializer, isClient]);

  // State to store value
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (initializeWithValue) {
      return readValue();
    }
    return defaultValue;
  });

  // Write to localStorage
  const setValue = useCallback(
    (value: SetValue<T>) => {
      if (!isClient) {
        console.warn('localStorage not available');
        return;
      }

      try {
        // Get new value
        const newValue = value instanceof Function ? value(storedValue) : value;

        // Save to localStorage
        if (newValue === undefined) {
          window.localStorage.removeItem(key);
        } else {
          window.localStorage.setItem(key, serializer(newValue));
        }

        // Update state
        setStoredValue(newValue);

        // Dispatch custom event for same-document sync
        window.dispatchEvent(
          new StorageEvent('storage', {
            key,
            newValue: serializer(newValue),
            storageArea: window.localStorage,
          }),
        );
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue, serializer, isClient],
  );

  // Remove from localStorage
  const removeValue = useCallback(() => {
    if (!isClient) return;

    try {
      window.localStorage.removeItem(key);
      setStoredValue(defaultValue);

      window.dispatchEvent(
        new StorageEvent('storage', {
          key,
          newValue: null,
          storageArea: window.localStorage,
        }),
      );
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, defaultValue, isClient]);

  // Listen for storage changes (cross-tab sync)
  useEffect(() => {
    if (!isClient) return;

    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === key && event.storageArea === window.localStorage) {
        try {
          if (event.newValue === null) {
            setStoredValue(defaultValue);
          } else {
            setStoredValue(deserializer(event.newValue));
          }
        } catch (error) {
          console.warn(`Error handling storage change for "${key}":`, error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, defaultValue, deserializer, isClient]);

  return [storedValue, setValue, removeValue];
}

export default useLocalStorage;
