/**
 * Radix Dropdown Menu - TypeScript Types
 *
 * Type definitions for the pre-styled Radix Dropdown Menu component.
 * Includes menu items, checkboxes, radio groups, separators, and submenus.
 *
 * @packageDocumentation
 */

import type { ReactNode, HTMLAttributes, ButtonHTMLAttributes } from 'react';

// =============================================================================
// COMMON TYPES
// =============================================================================

/** Generic children type for components */
type Children = ReactNode;

/** Menu alignment options */
export type MenuAlign = 'start' | 'center' | 'end';

/** Menu side options */
export type MenuSide = 'top' | 'right' | 'bottom' | 'left';

/** Item variant for styling */
export type ItemVariant = 'default' | 'destructive';

// =============================================================================
// DROPDOWN MENU ROOT TYPES
// =============================================================================

/** Props for the DropdownMenu root component */
export interface DropdownMenuProps {
  /** Menu content including trigger and portal content */
  children: Children;
  /** Controlled open state */
  open?: boolean;
  /** Callback when open state changes */
  onOpenChange?: (open: boolean) => void;
  /** Default open state for uncontrolled usage */
  defaultOpen?: boolean;
  /** Whether menu is modal (default: true) */
  modal?: boolean;
  /** Reading direction for RTL support */
  dir?: 'ltr' | 'rtl';
}

// =============================================================================
// DROPDOWN MENU TRIGGER TYPES
// =============================================================================

/** Props for the DropdownMenuTrigger component */
export interface DropdownMenuTriggerProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Trigger element */
  children: Children;
  /** Render as child element instead of button */
  asChild?: boolean;
}

// =============================================================================
// DROPDOWN MENU CONTENT TYPES
// =============================================================================

/** Props for the DropdownMenuContent component */
export interface DropdownMenuContentProps extends HTMLAttributes<HTMLDivElement> {
  /** Menu content */
  children: Children;
  /** Alignment relative to trigger */
  align?: MenuAlign;
  /** Side relative to trigger */
  side?: MenuSide;
  /** Offset from trigger (in pixels) */
  sideOffset?: number;
  /** Alignment offset (in pixels) */
  alignOffset?: number;
  /** Additional CSS classes */
  className?: string;
  /** Prevent closing when clicking outside */
  preventCloseOnOutsideClick?: boolean;
  /** Prevent closing on escape */
  preventCloseOnEscape?: boolean;
  /** Collision boundary */
  collisionBoundary?: Element | null;
  /** Collision padding */
  collisionPadding?: number;
  /** Whether to loop focus */
  loop?: boolean;
}

// =============================================================================
// DROPDOWN MENU ITEM TYPES
// =============================================================================

/** Props for the DropdownMenuItem component */
export interface DropdownMenuItemProps extends HTMLAttributes<HTMLDivElement> {
  /** Item content */
  children: Children;
  /** Whether item is disabled */
  disabled?: boolean;
  /** Visual variant */
  variant?: ItemVariant;
  /** Leading icon */
  icon?: Children;
  /** Keyboard shortcut display */
  shortcut?: string;
  /** Callback when item is selected */
  onSelect?: (event: Event) => void;
  /** Additional CSS classes */
  className?: string;
  /** Prevent menu from closing on select */
  preventClose?: boolean;
}

// =============================================================================
// DROPDOWN MENU CHECKBOX TYPES
// =============================================================================

/** Props for the DropdownMenuCheckboxItem component */
export interface DropdownMenuCheckboxItemProps extends HTMLAttributes<HTMLDivElement> {
  /** Item content */
  children: Children;
  /** Checked state */
  checked?: boolean;
  /** Callback when checked state changes */
  onCheckedChange?: (checked: boolean) => void;
  /** Whether item is disabled */
  disabled?: boolean;
  /** Additional CSS classes */
  className?: string;
}

// =============================================================================
// DROPDOWN MENU RADIO TYPES
// =============================================================================

/** Props for the DropdownMenuRadioGroup component */
export interface DropdownMenuRadioGroupProps {
  /** Radio items */
  children: Children;
  /** Current value */
  value?: string;
  /** Callback when value changes */
  onValueChange?: (value: string) => void;
}

/** Props for the DropdownMenuRadioItem component */
export interface DropdownMenuRadioItemProps extends HTMLAttributes<HTMLDivElement> {
  /** Item content */
  children: Children;
  /** Item value */
  value: string;
  /** Whether item is disabled */
  disabled?: boolean;
  /** Additional CSS classes */
  className?: string;
}

// =============================================================================
// DROPDOWN MENU LABEL & SEPARATOR TYPES
// =============================================================================

/** Props for the DropdownMenuLabel component */
export interface DropdownMenuLabelProps {
  /** Label text */
  children: Children;
  /** Whether label is inset (for alignment with icons) */
  inset?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/** Props for the DropdownMenuSeparator component */
export interface DropdownMenuSeparatorProps {
  /** Additional CSS classes */
  className?: string;
}

// =============================================================================
// DROPDOWN MENU SUBMENU TYPES
// =============================================================================

/** Props for the DropdownMenuSub component */
export interface DropdownMenuSubProps {
  /** Submenu content */
  children: Children;
  /** Controlled open state */
  open?: boolean;
  /** Callback when open state changes */
  onOpenChange?: (open: boolean) => void;
  /** Default open state */
  defaultOpen?: boolean;
}

/** Props for the DropdownMenuSubTrigger component */
export interface DropdownMenuSubTriggerProps extends HTMLAttributes<HTMLDivElement> {
  /** Trigger content */
  children: Children;
  /** Whether trigger is disabled */
  disabled?: boolean;
  /** Leading icon */
  icon?: Children;
  /** Additional CSS classes */
  className?: string;
}

/** Props for the DropdownMenuSubContent component */
export interface DropdownMenuSubContentProps extends HTMLAttributes<HTMLDivElement> {
  /** Submenu content */
  children: Children;
  /** Alignment relative to trigger */
  alignOffset?: number;
  /** Side offset */
  sideOffset?: number;
  /** Additional CSS classes */
  className?: string;
  /** Whether to loop focus */
  loop?: boolean;
}

// =============================================================================
// DROPDOWN MENU GROUP TYPES
// =============================================================================

/** Props for the DropdownMenuGroup component */
export interface DropdownMenuGroupProps {
  /** Group content */
  children: Children;
}

// =============================================================================
// STYLE MAPPINGS
// =============================================================================

/** Item variant styles */
export const ITEM_VARIANT_STYLES: Record<ItemVariant, string> = {
  default: 'text-text-primary focus:bg-surface-elevated',
  destructive: 'text-error focus:bg-error/10 focus:text-error',
} as const;

/** Animation classes for dropdown menu */
export const MENU_ANIMATIONS = {
  content: {
    enter: 'animate-in fade-in-0 zoom-in-95',
    exit: 'animate-out fade-out-0 zoom-out-95',
    base: 'duration-150',
  },
  side: {
    top: 'slide-in-from-bottom-2',
    right: 'slide-in-from-left-2',
    bottom: 'slide-in-from-top-2',
    left: 'slide-in-from-right-2',
  },
} as const;
