/**
 * Radix Dropdown Menu - Component Exports
 *
 * Central export file for all Radix Dropdown Menu components and types.
 *
 * @example
 * ```tsx
 * import {
 *   DropdownMenu,
 *   DropdownMenuTrigger,
 *   DropdownMenuContent,
 *   DropdownMenuItem,
 *   DropdownMenuCheckboxItem,
 *   DropdownMenuRadioGroup,
 *   DropdownMenuRadioItem,
 *   DropdownMenuLabel,
 *   DropdownMenuSeparator,
 *   DropdownMenuSub,
 *   DropdownMenuSubTrigger,
 *   DropdownMenuSubContent,
 *   DropdownMenuGroup,
 * } from './radix-dropdown';
 * ```
 *
 * @packageDocumentation
 */

// =============================================================================
// COMPONENT EXPORTS
// =============================================================================

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuGroup,
} from './DropdownMenu';

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export type {
  MenuAlign,
  MenuSide,
  ItemVariant,
  DropdownMenuProps,
  DropdownMenuTriggerProps,
  DropdownMenuContentProps,
  DropdownMenuItemProps,
  DropdownMenuCheckboxItemProps,
  DropdownMenuRadioGroupProps,
  DropdownMenuRadioItemProps,
  DropdownMenuLabelProps,
  DropdownMenuSeparatorProps,
  DropdownMenuSubProps,
  DropdownMenuSubTriggerProps,
  DropdownMenuSubContentProps,
  DropdownMenuGroupProps,
} from './types';

// =============================================================================
// CONSTANT EXPORTS
// =============================================================================

export { ITEM_VARIANT_STYLES, MENU_ANIMATIONS } from './types';
