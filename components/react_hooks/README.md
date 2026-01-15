# React Hooks Library

Production-ready React hooks for common patterns. All hooks are SSR-compatible, fully typed with TypeScript, and designed for LEGO-style composition.

## Installation

```bash
npm install react
# TypeScript users: types included
```

## Features

- **SSR-Compatible**: Safe for Next.js, Remix, and other SSR frameworks
- **TypeScript**: Full type safety with strict typing
- **Cross-Tab Sync**: localStorage changes sync across browser tabs
- **Race Condition Prevention**: Async hooks handle concurrent requests safely
- **Abortable**: Full AbortController support for cancellation
- **Flexible**: Debounce and throttle with leading/trailing edge control

## Hooks

### useLocalStorage

Persist React state to localStorage with cross-tab sync.

```tsx
import { useLocalStorage } from '@library/react-hooks';

function ThemeToggle() {
  const { value: theme, setValue: setTheme, remove } = useLocalStorage('theme', 'dark');
  return (
    <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
      {theme}
    </button>
  );
}
```

### useAsyncState

Manage async operations with loading/error states.

```tsx
import { useAsyncState } from '@library/react-hooks';

function UserProfile({ userId }) {
  const { data, isLoading, error, execute } = useAsyncState();
  useEffect(() => {
    execute(async () => {
      const res = await fetch(`/api/users/${userId}`);
      return res.json();
    });
  }, [userId, execute]);
  if (isLoading) return <Spinner />;
  return <Profile user={data} />;
}
```

### useAbortableAsync

Async state with AbortController support.

```tsx
import { useAbortableAsync } from '@library/react-hooks';

function Search({ query }) {
  const { data, execute, abort } = useAbortableAsync();
  useEffect(() => {
    execute(async (signal) => {
      const res = await fetch(`/api/search?q=${query}`, { signal });
      return res.json();
    });
    return () => abort();
  }, [query]);
}
```

### useDebounce / useDebouncedCallback

Debounce values or callbacks.

```tsx
import { useDebounce, useDebouncedCallback } from '@library/react-hooks';

// Value debounce
const { debouncedValue, isPending } = useDebounce(search, { delay: 300 });

// Callback debounce
const { debouncedCallback, flush } = useDebouncedCallback(save, { delay: 1000 });
```

### useThrottle / useThrottledCallback

Throttle values or callbacks.

```tsx
import { useThrottle, useThrottledCallback } from '@library/react-hooks';

// Value throttle
const { throttledValue, isThrottled } = useThrottle(scrollY, { interval: 100 });

// Callback throttle
const { throttledCallback } = useThrottledCallback(handleScroll, { interval: 150 });
```

## Sources

- [usehooks-ts](https://github.com/juliencrn/usehooks-ts)
- [use-local-storage-state](https://github.com/astoilkov/use-local-storage-state)
