/**
 * Kanban Store - Main Entry Point
 *
 * Generic, reusable Kanban board state management using Zustand.
 * Supports configurable columns, persistence abstraction, and full TypeScript support.
 *
 * @module kanban-store
 * @version 1.0.0
 * @license MIT
 *
 * @example
 * ```typescript
 * import {
 *   createKanbanStore,
 *   createApiPersistenceAdapter,
 *   type KanbanItemBase,
 *   type KanbanColumnConfig,
 * } from '@library/components/state/kanban-store';
 *
 * // 1. Define your item type
 * interface Task extends KanbanItemBase {
 *   id: string;
 *   title: string;
 *   status: 'backlog' | 'todo' | 'in_progress' | 'done';
 *   assignee?: string;
 * }
 *
 * // 2. Define columns
 * const COLUMNS: KanbanColumnConfig<Task['status']>[] = [
 *   { id: 'backlog', title: 'Backlog', color: '#9ca3af' },
 *   { id: 'todo', title: 'To Do', color: '#6b7280' },
 *   { id: 'in_progress', title: 'In Progress', color: '#3b82f6' },
 *   { id: 'done', title: 'Done', color: '#10b981' },
 * ];
 *
 * // 3. Create persistence adapter (optional)
 * const persistence = createApiPersistenceAdapter<Task, Task['status']>({
 *   baseUrl: 'https://api.example.com',
 *   endpoints: { list: '/tasks', update: (id) => `/tasks/${id}` },
 *   columnField: 'status',
 * });
 *
 * // 4. Create store
 * export const useTaskKanban = createKanbanStore<Task, Task['status']>({
 *   columns: COLUMNS,
 *   getItemColumn: (task) => task.status,
 *   persistence,
 * });
 *
 * // 5. Use in components
 * function KanbanBoard() {
 *   const { columns, moveItem, fetchItems, isLoading } = useTaskKanban();
 *
 *   useEffect(() => { fetchItems(); }, []);
 *
 *   return isLoading ? <Spinner /> : <Board columns={columns} onMove={moveItem} />;
 * }
 * ```
 */

// ============================================================================
// TYPE EXPORTS
// ============================================================================

export type {
  // Core types
  KanbanItemBase,
  KanbanColumnConfig,
  KanbanColumn,
  KanbanDragItem,

  // Store types
  KanbanStore,
  KanbanStoreState,
  KanbanStoreActions,

  // Persistence types
  KanbanPersistenceAdapter,
  NoPersistence,

  // Configuration types
  CreateKanbanStoreOptions,
  ColumnExtractor,

  // Utility types
  OrganizedColumns,
  StatusMapping,
  ExtractColumnId,
  ColumnData,
  BoardStats,
} from './types';

// ============================================================================
// FUNCTION EXPORTS
// ============================================================================

export {
  // Main factory
  createKanbanStore,

  // Persistence adapters
  createApiPersistenceAdapter,
  createLocalStoragePersistenceAdapter,

  // Helper functions
  createEmptyColumns,
  organizeItemsByColumn,
  findItemInColumns,

  // Selectors
  selectColumn,
  selectTotalCount,
  selectColumnCounts,
  selectItemById,
} from './kanban_store';

// ============================================================================
// PRESETS
// ============================================================================

/**
 * Default 3-column Kanban configuration (To Do, Doing, Done).
 */
export const DEFAULT_3_COLUMN_CONFIG = [
  { id: 'todo', title: 'To Do', color: '#6b7280' },
  { id: 'doing', title: 'Doing', color: '#3b82f6' },
  { id: 'done', title: 'Done', color: '#10b981' },
] as const;

/**
 * Default 4-column Kanban configuration (Backlog, To Do, In Progress, Done).
 */
export const DEFAULT_4_COLUMN_CONFIG = [
  { id: 'backlog', title: 'Backlog', color: '#9ca3af' },
  { id: 'todo', title: 'To Do', color: '#6b7280' },
  { id: 'in_progress', title: 'In Progress', color: '#3b82f6' },
  { id: 'done', title: 'Done', color: '#10b981' },
] as const;

/**
 * Default 5-column Kanban configuration (matching Life-OS workflow).
 */
export const DEFAULT_5_COLUMN_CONFIG = [
  { id: 'todo', title: 'To Do', color: '#6b7280' },
  { id: 'in_progress', title: 'In Progress', color: '#3b82f6' },
  { id: 'in_review', title: 'In Review', color: '#f59e0b' },
  { id: 'done', title: 'Done', color: '#10b981' },
  { id: 'cancelled', title: 'Cancelled', color: '#ef4444' },
] as const;

/**
 * Agile/Scrum column configuration.
 */
export const SCRUM_COLUMN_CONFIG = [
  { id: 'backlog', title: 'Product Backlog', color: '#9ca3af' },
  { id: 'sprint_backlog', title: 'Sprint Backlog', color: '#6b7280' },
  { id: 'in_progress', title: 'In Progress', color: '#3b82f6', wipLimit: 3 },
  { id: 'testing', title: 'Testing', color: '#f59e0b', wipLimit: 2 },
  { id: 'done', title: 'Done', color: '#10b981' },
] as const;

/**
 * Software development pipeline configuration.
 */
export const DEV_PIPELINE_CONFIG = [
  { id: 'idea', title: 'Idea', color: '#a855f7' },
  { id: 'design', title: 'Design', color: '#ec4899' },
  { id: 'development', title: 'Development', color: '#3b82f6' },
  { id: 'code_review', title: 'Code Review', color: '#f59e0b' },
  { id: 'testing', title: 'Testing', color: '#14b8a6' },
  { id: 'staging', title: 'Staging', color: '#8b5cf6' },
  { id: 'production', title: 'Production', color: '#10b981' },
] as const;

// ============================================================================
// TYPE HELPERS FOR PRESETS
// ============================================================================

/** Column ID type for 3-column config */
export type Default3ColumnId = (typeof DEFAULT_3_COLUMN_CONFIG)[number]['id'];

/** Column ID type for 4-column config */
export type Default4ColumnId = (typeof DEFAULT_4_COLUMN_CONFIG)[number]['id'];

/** Column ID type for 5-column config */
export type Default5ColumnId = (typeof DEFAULT_5_COLUMN_CONFIG)[number]['id'];

/** Column ID type for Scrum config */
export type ScrumColumnId = (typeof SCRUM_COLUMN_CONFIG)[number]['id'];

/** Column ID type for dev pipeline config */
export type DevPipelineColumnId = (typeof DEV_PIPELINE_CONFIG)[number]['id'];
