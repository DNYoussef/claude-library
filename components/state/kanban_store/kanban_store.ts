/**
 * Kanban Store - Generic Zustand Store Factory
 *
 * Creates a fully-typed Kanban board state management store using Zustand.
 * Supports configurable columns, persistence abstraction, and optimistic updates.
 *
 * @module kanban-store/kanban_store
 * @version 1.0.0
 * @license MIT
 *
 * @example
 * ```typescript
 * // Define your item type
 * interface MyTask extends KanbanItemBase {
 *   id: string;
 *   title: string;
 *   status: 'todo' | 'doing' | 'done';
 * }
 *
 * // Define columns
 * const columns = [
 *   { id: 'todo', title: 'To Do', color: '#6b7280' },
 *   { id: 'doing', title: 'In Progress', color: '#3b82f6' },
 *   { id: 'done', title: 'Done', color: '#10b981' },
 * ] as const;
 *
 * // Create store
 * const useTaskKanban = createKanbanStore<MyTask, 'todo' | 'doing' | 'done'>({
 *   columns,
 *   getItemColumn: (task) => task.status,
 *   persistence: myApiAdapter,
 * });
 * ```
 */

import { create, StateCreator } from 'zustand';
import type {
  KanbanItemBase,
  KanbanColumnConfig,
  KanbanStore,
  KanbanStoreState,
  KanbanPersistenceAdapter,
  CreateKanbanStoreOptions,
  OrganizedColumns,
  ColumnExtractor,
  NoPersistence,
} from './types';

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Creates an empty columns record from column configs.
 *
 * @template TItem - Item type
 * @template TColumnId - Column ID type
 * @param columns - Column configurations
 * @returns Empty columns record
 */
export function createEmptyColumns<
  TItem extends KanbanItemBase,
  TColumnId extends string
>(columns: KanbanColumnConfig<TColumnId>[]): OrganizedColumns<TItem, TColumnId> {
  const result = {} as OrganizedColumns<TItem, TColumnId>;
  for (const col of columns) {
    result[col.id] = [];
  }
  return result;
}

/**
 * Organizes items into columns based on extractor function.
 *
 * @template TItem - Item type
 * @template TColumnId - Column ID type
 * @param items - Items to organize
 * @param columns - Column configurations
 * @param getItemColumn - Function to extract column ID from item
 * @param defaultColumn - Default column for items with unknown column
 * @returns Organized columns record
 */
export function organizeItemsByColumn<
  TItem extends KanbanItemBase,
  TColumnId extends string
>(
  items: TItem[],
  columns: KanbanColumnConfig<TColumnId>[],
  getItemColumn: ColumnExtractor<TItem, TColumnId>,
  defaultColumn: TColumnId
): OrganizedColumns<TItem, TColumnId> {
  const result = createEmptyColumns<TItem, TColumnId>(columns);
  const validColumnIds = new Set(columns.map((c) => c.id));

  for (const item of items) {
    let columnId = getItemColumn(item);

    // Fallback to default if column doesn't exist
    if (!validColumnIds.has(columnId)) {
      columnId = defaultColumn;
    }

    result[columnId].push(item);
  }

  return result;
}

/**
 * Finds an item across all columns.
 *
 * @template TItem - Item type
 * @template TColumnId - Column ID type
 * @param columns - Columns to search
 * @param itemId - ID of item to find
 * @returns Tuple of [item, columnId] or null if not found
 */
export function findItemInColumns<
  TItem extends KanbanItemBase,
  TColumnId extends string
>(
  columns: OrganizedColumns<TItem, TColumnId>,
  itemId: string
): [TItem, TColumnId] | null {
  for (const columnId of Object.keys(columns) as TColumnId[]) {
    const item = columns[columnId].find((i) => i.id === itemId);
    if (item) {
      return [item, columnId];
    }
  }
  return null;
}

// ============================================================================
// STORE FACTORY
// ============================================================================

/**
 * Creates a Kanban store with the provided configuration.
 *
 * @template TItem - The item type (must extend KanbanItemBase)
 * @template TColumnId - String literal union of valid column IDs
 * @param options - Store configuration options
 * @returns Zustand hook for the Kanban store
 *
 * @example
 * ```typescript
 * const useKanban = createKanbanStore<Task, TaskStatus>({
 *   columns: TASK_COLUMNS,
 *   getItemColumn: (task) => task.status,
 *   persistence: apiAdapter,
 * });
 *
 * // In component:
 * const { columns, moveItem, isLoading } = useKanban();
 * ```
 */
export function createKanbanStore<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
>(options: CreateKanbanStoreOptions<TItem, TColumnId>) {
  // [C1] Validate columns array is non-empty before accessing
  if (!options.columns || options.columns.length === 0) {
    throw new Error(
      'createKanbanStore: columns array must not be empty. ' +
      'Provide at least one column configuration with { id, title }.'
    );
  }

  const {
    columns,
    getItemColumn,
    defaultColumn = columns[0].id as TColumnId,
    persistence = null,
    fallbackItems = [],
    showErrorOnFallback = false,
    onItemsChange,
    onItemMove,
  } = options;

  // Create initial state
  const initialState: KanbanStoreState<TItem, TColumnId> = {
    columns: createEmptyColumns<TItem, TColumnId>(columns),
    isLoading: false,
    error: null,
    activeItem: null,
    columnConfigs: columns,
  };

  // Create store
  const storeCreator: StateCreator<KanbanStore<TItem, TColumnId>> = (
    set,
    get
  ) => ({
    ...initialState,

    fetchItems: async () => {
      if (!persistence) {
        // No persistence - use fallback items
        const organized = organizeItemsByColumn(
          fallbackItems,
          columns,
          getItemColumn,
          defaultColumn
        );
        set({ columns: organized, isLoading: false });
        return;
      }

      set({ isLoading: true, error: null });

      try {
        const items = await persistence.fetchItems();
        const organized = organizeItemsByColumn(
          items,
          columns,
          getItemColumn,
          defaultColumn
        );
        set({ columns: organized, isLoading: false });
        onItemsChange?.(organized);
      } catch (error) {
        // Use fallback on error
        const organized = organizeItemsByColumn(
          fallbackItems,
          columns,
          getItemColumn,
          defaultColumn
        );

        set({
          columns: organized,
          isLoading: false,
          error: showErrorOnFallback
            ? error instanceof Error
              ? error.message
              : 'Failed to fetch items'
            : null,
        });
        onItemsChange?.(organized);
      }
    },

    moveItem: (
      itemId: string,
      fromColumn: TColumnId,
      toColumn: TColumnId,
      newIndex?: number
    ) => {
      const { columns: currentColumns } = get();

      // Find and remove from source
      const sourceItems = [...currentColumns[fromColumn]];
      const itemIndex = sourceItems.findIndex((i) => i.id === itemId);

      // [H3] Return boolean indicating success instead of silent failure
      if (itemIndex === -1) {
        console.warn(`Item ${itemId} not found in column ${fromColumn}`);
        return false;
      }

      const [item] = sourceItems.splice(itemIndex, 1);

      // Add to destination
      const destItems = [...currentColumns[toColumn]];
      if (newIndex !== undefined && newIndex >= 0) {
        destItems.splice(newIndex, 0, item);
      } else {
        destItems.push(item);
      }

      const newColumns = {
        ...currentColumns,
        [fromColumn]: sourceItems,
        [toColumn]: destItems,
      };

      set({ columns: newColumns });
      onItemsChange?.(newColumns);
      onItemMove?.(itemId, fromColumn, toColumn);
      return true; // [H3] Return success
    },

    updateItemColumn: async (itemId: string, newColumn: TColumnId) => {
      if (!persistence) return;

      // [H4] Capture state snapshot for optimistic update rollback
      const previousColumns = { ...get().columns };
      // Deep copy the affected arrays to prevent mutation
      for (const colId of Object.keys(previousColumns) as TColumnId[]) {
        previousColumns[colId] = [...previousColumns[colId]];
      }

      try {
        await persistence.updateItemColumn(itemId, newColumn);
      } catch (error) {
        // [H4] Rollback to snapshot instead of refetching
        set({
          columns: previousColumns,
          error:
            error instanceof Error ? error.message : 'Failed to update item',
        });
        // Notify listeners of the rollback
        onItemsChange?.(previousColumns);
      }
    },

    setActiveItem: (item: TItem | null) => {
      set({ activeItem: item });
    },

    addItem: (item: TItem, columnId?: TColumnId) => {
      const { columns: currentColumns } = get();
      const targetColumn = columnId || getItemColumn(item) || defaultColumn;

      const newColumns = {
        ...currentColumns,
        [targetColumn]: [...currentColumns[targetColumn], item],
      };

      set({ columns: newColumns });
      onItemsChange?.(newColumns);
    },

    removeItem: (itemId: string) => {
      const { columns: currentColumns } = get();
      const newColumns = { ...currentColumns };

      for (const colId of Object.keys(newColumns) as TColumnId[]) {
        const filtered = newColumns[colId].filter((i) => i.id !== itemId);
        if (filtered.length !== newColumns[colId].length) {
          newColumns[colId] = filtered;
          break;
        }
      }

      set({ columns: newColumns });
      onItemsChange?.(newColumns);
    },

    updateItem: (itemId: string, updates: Partial<TItem>) => {
      const { columns: currentColumns } = get();
      const newColumns = { ...currentColumns };

      for (const colId of Object.keys(newColumns) as TColumnId[]) {
        const index = newColumns[colId].findIndex((i) => i.id === itemId);
        if (index !== -1) {
          newColumns[colId] = [...newColumns[colId]];
          newColumns[colId][index] = {
            ...newColumns[colId][index],
            ...updates,
          };
          break;
        }
      }

      set({ columns: newColumns });
      onItemsChange?.(newColumns);
    },

    reorderInColumn: (
      columnId: TColumnId,
      fromIndex: number,
      toIndex: number
    ) => {
      const { columns: currentColumns } = get();
      const items = [...currentColumns[columnId]];

      if (
        fromIndex < 0 ||
        fromIndex >= items.length ||
        toIndex < 0 ||
        toIndex >= items.length
      ) {
        return;
      }

      const [item] = items.splice(fromIndex, 1);
      items.splice(toIndex, 0, item);

      const newColumns = {
        ...currentColumns,
        [columnId]: items,
      };

      set({ columns: newColumns });
      onItemsChange?.(newColumns);
    },

    clearError: () => {
      set({ error: null });
    },

    reset: () => {
      set(initialState);
    },
  });

  return create<KanbanStore<TItem, TColumnId>>(storeCreator);
}

// ============================================================================
// PERSISTENCE ADAPTERS
// ============================================================================

/**
 * Creates an API-based persistence adapter.
 *
 * @template TItem - Item type
 * @template TColumnId - Column ID type
 * @param config - API configuration
 * @returns Persistence adapter
 *
 * @example
 * ```typescript
 * const apiAdapter = createApiPersistenceAdapter<Task, TaskStatus>({
 *   baseUrl: 'https://api.example.com',
 *   endpoints: {
 *     list: '/tasks',
 *     update: (id) => `/tasks/${id}`,
 *   },
 *   columnField: 'status',
 * });
 * ```
 */
export function createApiPersistenceAdapter<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
>(config: {
  baseUrl: string;
  endpoints: {
    list: string;
    update: (id: string) => string;
    create?: string;
    delete?: (id: string) => string;
  };
  columnField: keyof TItem;
  headers?: Record<string, string>;
  parseResponse?: (data: unknown) => TItem[];
}): KanbanPersistenceAdapter<TItem, TColumnId> {
  const {
    baseUrl,
    endpoints,
    columnField,
    headers = { 'Content-Type': 'application/json' },
    parseResponse = (data: unknown) => {
      if (Array.isArray(data)) return data as TItem[];
      if (typeof data === 'object' && data !== null && 'items' in data) {
        return (data as { items: TItem[] }).items;
      }
      return [];
    },
  } = config;

  return {
    fetchItems: async () => {
      const response = await fetch(`${baseUrl}${endpoints.list}`, { headers });
      if (!response.ok) {
        throw new Error(`Failed to fetch items: ${response.statusText}`);
      }
      const data = await response.json();
      return parseResponse(data);
    },

    updateItemColumn: async (itemId: string, newColumnId: TColumnId) => {
      const response = await fetch(`${baseUrl}${endpoints.update(itemId)}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ [columnField]: newColumnId }),
      });
      if (!response.ok) {
        throw new Error(`Failed to update item: ${response.statusText}`);
      }
    },

    createItem: endpoints.create
      ? async (item: Omit<TItem, 'id'>) => {
          const response = await fetch(`${baseUrl}${endpoints.create}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(item),
          });
          if (!response.ok) {
            throw new Error(`Failed to create item: ${response.statusText}`);
          }
          // [H5] Add try-catch around JSON parsing to handle response body errors
          try {
            return await response.json();
          } catch (parseError) {
            throw new Error(
              `Failed to parse create response: ${parseError instanceof Error ? parseError.message : 'Invalid JSON'}`
            );
          }
        }
      : undefined,

    deleteItem: endpoints.delete
      ? async (itemId: string) => {
          const response = await fetch(`${baseUrl}${endpoints.delete!(itemId)}`, {
            method: 'DELETE',
            headers,
          });
          if (!response.ok) {
            throw new Error(`Failed to delete item: ${response.statusText}`);
          }
        }
      : undefined,
  };
}

/**
 * Creates a localStorage-based persistence adapter.
 *
 * @template TItem - Item type
 * @template TColumnId - Column ID type
 * @param storageKey - Key to use in localStorage
 * @param columnField - Field name containing column ID
 * @returns Persistence adapter
 *
 * @example
 * ```typescript
 * const localAdapter = createLocalStoragePersistenceAdapter<Task, TaskStatus>(
 *   'my-kanban-tasks',
 *   'status'
 * );
 * ```
 */
// [M4] Helper function with proper typing for localStorage column updates
function updateItemColumnField<TItem extends KanbanItemBase>(
  item: TItem,
  columnField: keyof TItem,
  newValue: string
): TItem {
  return {
    ...item,
    [columnField]: newValue,
  };
}

export function createLocalStoragePersistenceAdapter<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
>(
  storageKey: string,
  columnField: keyof TItem
): KanbanPersistenceAdapter<TItem, TColumnId> {
  // [M5] Improved error handling with specific error types
  const getItems = (): TItem[] => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (!stored) return [];
      return JSON.parse(stored) as TItem[];
    } catch (error) {
      // Handle specific error types
      if (error instanceof SyntaxError) {
        console.error(
          `[kanban-store] Invalid JSON in localStorage key "${storageKey}":`,
          error.message
        );
      } else if (error instanceof DOMException) {
        // SecurityError: blocked by browser security settings
        // QuotaExceededError: storage quota exceeded
        console.error(
          `[kanban-store] localStorage access error for key "${storageKey}":`,
          error.name,
          error.message
        );
      } else {
        console.error(
          `[kanban-store] Unknown error reading from localStorage key "${storageKey}":`,
          error
        );
      }
      return [];
    }
  };

  const saveItems = (items: TItem[]) => {
    localStorage.setItem(storageKey, JSON.stringify(items));
  };

  return {
    fetchItems: async () => {
      return getItems();
    },

    updateItemColumn: async (itemId: string, newColumnId: TColumnId) => {
      const items = getItems();
      const index = items.findIndex((i) => i.id === itemId);
      if (index !== -1) {
        // [M4] Use helper function instead of unsafe type assertion
        items[index] = updateItemColumnField(items[index], columnField, newColumnId);
        saveItems(items);
      }
    },

    createItem: async (item: Omit<TItem, 'id'>) => {
      const items = getItems();
      const newItem = {
        ...item,
        id: crypto.randomUUID(),
      } as TItem;
      items.push(newItem);
      saveItems(items);
      return newItem;
    },

    deleteItem: async (itemId: string) => {
      const items = getItems().filter((i) => i.id !== itemId);
      saveItems(items);
    },

    updateItem: async (itemId: string, updates: Partial<TItem>) => {
      const items = getItems();
      const index = items.findIndex((i) => i.id === itemId);
      if (index !== -1) {
        items[index] = { ...items[index], ...updates };
        saveItems(items);
        return items[index];
      }
      throw new Error(`Item ${itemId} not found`);
    },
  };
}

// ============================================================================
// SELECTOR HELPERS
// ============================================================================

/**
 * Creates a selector for a specific column's items.
 *
 * @template TItem - Item type
 * @template TColumnId - Column ID type
 * @param columnId - Column to select
 * @returns Selector function
 */
export function selectColumn<
  TItem extends KanbanItemBase,
  TColumnId extends string
>(columnId: TColumnId) {
  return (state: KanbanStore<TItem, TColumnId>) => state.columns[columnId];
}

/**
 * Creates a selector for total item count.
 *
 * @template TItem - Item type
 * @template TColumnId - Column ID type
 * @returns Selector function
 */
export function selectTotalCount<
  TItem extends KanbanItemBase,
  TColumnId extends string
>() {
  return (state: KanbanStore<TItem, TColumnId>) => {
    const columnValues = Object.values(state.columns) as TItem[][];
    return columnValues.reduce((sum, items) => sum + items.length, 0);
  };
}

/**
 * Creates a selector for column counts.
 *
 * @template TItem - Item type
 * @template TColumnId - Column ID type
 * @returns Selector function
 */
export function selectColumnCounts<
  TItem extends KanbanItemBase,
  TColumnId extends string
>() {
  return (state: KanbanStore<TItem, TColumnId>) => {
    const counts = {} as Record<TColumnId, number>;
    for (const [colId, items] of Object.entries(state.columns)) {
      counts[colId as TColumnId] = (items as TItem[]).length;
    }
    return counts;
  };
}

/**
 * Creates a selector to find an item by ID.
 *
 * @template TItem - Item type
 * @template TColumnId - Column ID type
 * @param itemId - Item ID to find
 * @returns Selector function
 */
export function selectItemById<
  TItem extends KanbanItemBase,
  TColumnId extends string
>(itemId: string) {
  return (state: KanbanStore<TItem, TColumnId>) =>
    findItemInColumns(state.columns, itemId)?.[0] ?? null;
}
