/**
 * Kanban Store - TypeScript Types
 *
 * Generic type definitions for a reusable Kanban board state management system.
 * Designed to work with any item type and configurable columns.
 *
 * @module kanban-store/types
 * @version 1.0.0
 * @license MIT
 */

// ============================================================================
// CORE GENERIC TYPES
// ============================================================================

/**
 * Base interface that all Kanban items must implement.
 * Your custom item type should extend this interface.
 */
export interface KanbanItemBase {
  /** Unique identifier for the item */
  id: string;
}

/**
 * Configuration for a single Kanban column.
 *
 * @template TColumnId - String literal union type for column identifiers
 */
export interface KanbanColumnConfig<TColumnId extends string = string> {
  /** Unique identifier for the column */
  id: TColumnId;
  /** Display title for the column */
  title: string;
  /** Color associated with the column (hex, rgb, or CSS color name) */
  color: string;
  /** Optional maximum number of items allowed in column (WIP limit) */
  wipLimit?: number;
  /** Optional description or tooltip text */
  description?: string;
}

/**
 * A Kanban column with its items.
 *
 * @template TItem - The item type stored in columns
 * @template TColumnId - String literal union type for column identifiers
 */
export interface KanbanColumn<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
> {
  /** Column configuration */
  config: KanbanColumnConfig<TColumnId>;
  /** Items in this column */
  items: TItem[];
}

/**
 * Represents an item being dragged in the Kanban board.
 *
 * @template TColumnId - String literal union type for column identifiers
 */
export interface KanbanDragItem<TColumnId extends string = string> {
  /** ID of the item being dragged */
  id: string;
  /** Source column ID */
  sourceColumnId: TColumnId;
  /** Original index in source column */
  sourceIndex: number;
}

// ============================================================================
// PERSISTENCE LAYER TYPES
// ============================================================================

/**
 * Abstract persistence adapter interface.
 * Implement this to add custom persistence (API, localStorage, IndexedDB, etc.)
 *
 * @template TItem - The item type to persist
 * @template TColumnId - String literal union type for column identifiers
 */
export interface KanbanPersistenceAdapter<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
> {
  /** Fetch all items from persistent storage */
  fetchItems: () => Promise<TItem[]>;

  /** Update an item's column/status in persistent storage */
  updateItemColumn: (itemId: string, newColumnId: TColumnId) => Promise<void>;

  /** Optional: Create a new item */
  createItem?: (item: Omit<TItem, 'id'>) => Promise<TItem>;

  /** Optional: Delete an item */
  deleteItem?: (itemId: string) => Promise<void>;

  /** Optional: Update item properties */
  updateItem?: (itemId: string, updates: Partial<TItem>) => Promise<TItem>;

  /** Optional: Reorder items within a column */
  reorderItems?: (columnId: TColumnId, itemIds: string[]) => Promise<void>;
}

/**
 * No-op persistence adapter for client-only state.
 */
export type NoPersistence = null;

// ============================================================================
// STORE STATE TYPES
// ============================================================================

/**
 * Core Kanban store state (without actions).
 *
 * @template TItem - The item type stored in columns
 * @template TColumnId - String literal union type for column identifiers
 */
export interface KanbanStoreState<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
> {
  /** Items organized by column ID */
  columns: Record<TColumnId, TItem[]>;

  /** Whether data is currently being loaded */
  isLoading: boolean;

  /** Error message if last operation failed */
  error: string | null;

  /** Currently active/dragging item (null if none) */
  activeItem: TItem | null;

  /** Column configurations */
  columnConfigs: KanbanColumnConfig<TColumnId>[];
}

/**
 * Kanban store actions.
 *
 * @template TItem - The item type stored in columns
 * @template TColumnId - String literal union type for column identifiers
 */
export interface KanbanStoreActions<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
> {
  /** Fetch items from persistence layer and organize into columns */
  fetchItems: () => Promise<void>;

  /** Move an item between columns (optimistic update) */
  moveItem: (
    itemId: string,
    fromColumn: TColumnId,
    toColumn: TColumnId,
    newIndex?: number
  ) => void;

  /** Persist item column change to backend */
  updateItemColumn: (itemId: string, newColumn: TColumnId) => Promise<void>;

  /** Set the currently active/dragging item */
  setActiveItem: (item: TItem | null) => void;

  /** Add an item to a column */
  addItem: (item: TItem, columnId?: TColumnId) => void;

  /** Remove an item from all columns */
  removeItem: (itemId: string) => void;

  /** Update an item's properties */
  updateItem: (itemId: string, updates: Partial<TItem>) => void;

  /** Reorder items within a column */
  reorderInColumn: (columnId: TColumnId, fromIndex: number, toIndex: number) => void;

  /** Clear error state */
  clearError: () => void;

  /** Reset store to initial state */
  reset: () => void;
}

/**
 * Complete Kanban store type (state + actions).
 *
 * @template TItem - The item type stored in columns
 * @template TColumnId - String literal union type for column identifiers
 */
export type KanbanStore<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
> = KanbanStoreState<TItem, TColumnId> & KanbanStoreActions<TItem, TColumnId>;

// ============================================================================
// CONFIGURATION TYPES
// ============================================================================

/**
 * Function to extract column ID from an item.
 * Used when organizing items into columns.
 *
 * @template TItem - The item type
 * @template TColumnId - String literal union type for column identifiers
 */
export type ColumnExtractor<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
> = (item: TItem) => TColumnId;

/**
 * Configuration options for creating a Kanban store.
 *
 * @template TItem - The item type stored in columns
 * @template TColumnId - String literal union type for column identifiers
 */
export interface CreateKanbanStoreOptions<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
> {
  /** Column configurations defining available columns */
  columns: KanbanColumnConfig<TColumnId>[];

  /** Function to extract column ID from an item */
  getItemColumn: ColumnExtractor<TItem, TColumnId>;

  /** Default column for new items (defaults to first column) */
  defaultColumn?: TColumnId;

  /** Persistence adapter (null for client-only state) */
  persistence?: KanbanPersistenceAdapter<TItem, TColumnId> | NoPersistence;

  /** Optional fallback items when fetch fails */
  fallbackItems?: TItem[];

  /** Whether to show error or silently use fallback (default: false) */
  showErrorOnFallback?: boolean;

  /** Optional callback when items change */
  onItemsChange?: (columns: Record<TColumnId, TItem[]>) => void;

  /** Optional callback when an item moves */
  onItemMove?: (
    itemId: string,
    fromColumn: TColumnId,
    toColumn: TColumnId
  ) => void;
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

/**
 * Helper type to extract column IDs from column configs.
 */
export type ExtractColumnId<T extends KanbanColumnConfig<string>[]> =
  T[number]['id'];

/**
 * Type for a status mapping (legacy status to Kanban column).
 *
 * @template TLegacyStatus - Legacy status type
 * @template TColumnId - Kanban column ID type
 */
export type StatusMapping<
  TLegacyStatus extends string,
  TColumnId extends string
> = Record<TLegacyStatus, TColumnId>;

/**
 * Result of organizing items into columns.
 *
 * @template TItem - The item type
 * @template TColumnId - Column ID type
 */
export type OrganizedColumns<
  TItem extends KanbanItemBase,
  TColumnId extends string = string
> = Record<TColumnId, TItem[]>;

// ============================================================================
// HOOK RETURN TYPES
// ============================================================================

/**
 * Return type for column-specific selectors.
 *
 * @template TItem - The item type
 */
export interface ColumnData<TItem extends KanbanItemBase> {
  items: TItem[];
  count: number;
  isOverWipLimit: boolean;
}

/**
 * Return type for board statistics.
 */
export interface BoardStats {
  totalItems: number;
  itemsByColumn: Record<string, number>;
  completionRate: number;
}
