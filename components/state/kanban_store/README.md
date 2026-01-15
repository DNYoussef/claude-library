# Kanban Store

Generic, reusable Kanban board state management using Zustand. Fully typed with TypeScript support for custom item types and configurable columns.

## Features

- **Generic Item Type**: Works with any data structure that has an `id` field
- **Configurable Columns**: Define your own columns with custom IDs, titles, colors, and WIP limits
- **Persistence Abstraction**: Built-in adapters for API and localStorage, or create your own
- **Optimistic Updates**: Immediate UI updates with automatic rollback on failure
- **Full TypeScript Support**: Strongly typed stores, selectors, and helpers
- **Preset Configurations**: Ready-to-use column configs for common workflows

## Installation

This component requires `zustand` as a peer dependency:

```bash
npm install zustand
```

## Quick Start

```typescript
import {
  createKanbanStore,
  createApiPersistenceAdapter,
  DEFAULT_5_COLUMN_CONFIG,
  type KanbanItemBase,
} from '@library/components/state/kanban-store';

// 1. Define your item type (must have `id: string`)
interface Task extends KanbanItemBase {
  id: string;
  title: string;
  status: 'todo' | 'in_progress' | 'in_review' | 'done' | 'cancelled';
  priority?: 'low' | 'medium' | 'high';
}

// 2. Create the store
const useTaskKanban = createKanbanStore<Task, Task['status']>({
  columns: DEFAULT_5_COLUMN_CONFIG,
  getItemColumn: (task) => task.status,
  persistence: createApiPersistenceAdapter({
    baseUrl: 'https://api.example.com',
    endpoints: {
      list: '/tasks',
      update: (id) => `/tasks/${id}`,
    },
    columnField: 'status',
  }),
});

// 3. Use in React component
function KanbanBoard() {
  const { columns, moveItem, fetchItems, isLoading } = useTaskKanban();

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleDrop = (taskId: string, from: string, to: string) => {
    moveItem(taskId, from, to);
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="kanban-board">
      {Object.entries(columns).map(([columnId, tasks]) => (
        <Column key={columnId} id={columnId} tasks={tasks} onDrop={handleDrop} />
      ))}
    </div>
  );
}
```

## API Reference

### `createKanbanStore<TItem, TColumnId>(options)`

Creates a Zustand store for Kanban board state management.

**Type Parameters:**
- `TItem extends KanbanItemBase` - Your item type (must have `id: string`)
- `TColumnId extends string` - String literal union of valid column IDs

**Options:**

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `columns` | `KanbanColumnConfig<TColumnId>[]` | Yes | Column configurations |
| `getItemColumn` | `(item: TItem) => TColumnId` | Yes | Extract column ID from item |
| `defaultColumn` | `TColumnId` | No | Default column for new items |
| `persistence` | `KanbanPersistenceAdapter \| null` | No | Persistence adapter |
| `fallbackItems` | `TItem[]` | No | Items to use when fetch fails |
| `showErrorOnFallback` | `boolean` | No | Show error when using fallback |
| `onItemsChange` | `(columns) => void` | No | Callback when items change |
| `onItemMove` | `(id, from, to) => void` | No | Callback when item moves |

**Returns:** Zustand hook with the following state and actions:

#### State
- `columns: Record<TColumnId, TItem[]>` - Items organized by column
- `isLoading: boolean` - Loading state
- `error: string | null` - Error message
- `activeItem: TItem | null` - Currently dragged item
- `columnConfigs: KanbanColumnConfig[]` - Column configurations

#### Actions
- `fetchItems()` - Fetch items from persistence
- `moveItem(id, from, to, index?)` - Move item between columns
- `updateItemColumn(id, column)` - Persist column change
- `setActiveItem(item)` - Set active/dragging item
- `addItem(item, column?)` - Add item to column
- `removeItem(id)` - Remove item
- `updateItem(id, updates)` - Update item properties
- `reorderInColumn(column, from, to)` - Reorder within column
- `clearError()` - Clear error state
- `reset()` - Reset to initial state

### Persistence Adapters

#### `createApiPersistenceAdapter<TItem, TColumnId>(config)`

Creates an adapter for REST API persistence.

```typescript
const adapter = createApiPersistenceAdapter<Task, TaskStatus>({
  baseUrl: 'https://api.example.com',
  endpoints: {
    list: '/tasks',
    update: (id) => `/tasks/${id}`,
    create: '/tasks',           // Optional
    delete: (id) => `/tasks/${id}`, // Optional
  },
  columnField: 'status',
  headers: { Authorization: 'Bearer token' }, // Optional
  parseResponse: (data) => data.items,        // Optional
});
```

#### `createLocalStoragePersistenceAdapter<TItem, TColumnId>(key, field)`

Creates an adapter for localStorage persistence.

```typescript
const adapter = createLocalStoragePersistenceAdapter<Task, TaskStatus>(
  'my-kanban-tasks',
  'status'
);
```

### Selectors

```typescript
import {
  selectColumn,
  selectTotalCount,
  selectColumnCounts,
  selectItemById,
} from '@library/components/state/kanban-store';

// Select single column
const todoTasks = useTaskKanban(selectColumn('todo'));

// Select total count
const totalTasks = useTaskKanban(selectTotalCount());

// Select counts per column
const counts = useTaskKanban(selectColumnCounts());

// Find specific item
const task = useTaskKanban(selectItemById('task-123'));
```

### Column Presets

Ready-to-use column configurations:

```typescript
import {
  DEFAULT_3_COLUMN_CONFIG, // To Do, Doing, Done
  DEFAULT_4_COLUMN_CONFIG, // Backlog, To Do, In Progress, Done
  DEFAULT_5_COLUMN_CONFIG, // To Do, In Progress, In Review, Done, Cancelled
  SCRUM_COLUMN_CONFIG,     // Product Backlog, Sprint Backlog, In Progress, Testing, Done
  DEV_PIPELINE_CONFIG,     // Idea, Design, Development, Code Review, Testing, Staging, Production
} from '@library/components/state/kanban-store';
```

## Custom Persistence Adapter

Implement the `KanbanPersistenceAdapter` interface:

```typescript
import type { KanbanPersistenceAdapter } from '@library/components/state/kanban-store';

const customAdapter: KanbanPersistenceAdapter<MyTask, MyStatus> = {
  // Required
  fetchItems: async () => {
    const response = await myDatabase.query('SELECT * FROM tasks');
    return response.rows;
  },

  // Required
  updateItemColumn: async (itemId, newColumn) => {
    await myDatabase.update('tasks', { id: itemId }, { status: newColumn });
  },

  // Optional
  createItem: async (item) => {
    const id = crypto.randomUUID();
    await myDatabase.insert('tasks', { ...item, id });
    return { ...item, id };
  },

  // Optional
  deleteItem: async (itemId) => {
    await myDatabase.delete('tasks', { id: itemId });
  },

  // Optional
  updateItem: async (itemId, updates) => {
    await myDatabase.update('tasks', { id: itemId }, updates);
    return myDatabase.findOne('tasks', { id: itemId });
  },

  // Optional
  reorderItems: async (columnId, itemIds) => {
    await Promise.all(
      itemIds.map((id, index) =>
        myDatabase.update('tasks', { id }, { order: index })
      )
    );
  },
};
```

## TypeScript Types

All types are exported for use in your application:

```typescript
import type {
  // Core
  KanbanItemBase,
  KanbanColumnConfig,
  KanbanColumn,
  KanbanDragItem,

  // Store
  KanbanStore,
  KanbanStoreState,
  KanbanStoreActions,

  // Persistence
  KanbanPersistenceAdapter,

  // Configuration
  CreateKanbanStoreOptions,
  ColumnExtractor,

  // Utilities
  OrganizedColumns,
  StatusMapping,
  ColumnData,
  BoardStats,
} from '@library/components/state/kanban-store';
```

## Migration from Life-OS

If migrating from the original Life-OS implementation:

```typescript
// Before (Life-OS specific)
import { useKanbanStore } from '../stores/uiStore';
import type { Task, KanbanStatus } from '../types';

// After (Generic)
import {
  createKanbanStore,
  createApiPersistenceAdapter,
  DEFAULT_5_COLUMN_CONFIG,
} from '@library/components/state/kanban-store';

// Define Task type locally or import
interface Task { /* ... */ }
type KanbanStatus = 'todo' | 'in_progress' | 'in_review' | 'done' | 'cancelled';

export const useKanbanStore = createKanbanStore<Task, KanbanStatus>({
  columns: DEFAULT_5_COLUMN_CONFIG,
  getItemColumn: (task) => task.kanban_status || 'todo',
  persistence: createApiPersistenceAdapter({
    baseUrl: import.meta.env.VITE_API_URL,
    endpoints: {
      list: '/api/v1/tasks',
      update: (id) => `/api/v1/tasks/${id}`,
    },
    columnField: 'kanban_status',
  }),
});
```

## Source

Extracted from: `D:\Projects\life-os-frontend\src\stores\uiStore.ts`

## Version

1.0.0
