/**
 * Radix Dialog - TypeScript Types
 *
 * Type definitions for the pre-styled Radix Dialog component.
 * Includes Dialog, DialogTrigger, DialogContent, DialogHeader, DialogFooter.
 *
 * @packageDocumentation
 */

import type { ReactNode, HTMLAttributes, ButtonHTMLAttributes } from 'react';

// =============================================================================
// COMMON TYPES
// =============================================================================

/** Generic children type for components */
type Children = ReactNode;

/** Dialog size variants */
export type DialogSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

// =============================================================================
// DIALOG ROOT TYPES
// =============================================================================

/** Props for the Dialog root component */
export interface DialogProps {
  /** Dialog content including trigger and portal content */
  children: Children;
  /** Controlled open state */
  open?: boolean;
  /** Callback when open state changes */
  onOpenChange?: (open: boolean) => void;
  /** Default open state for uncontrolled usage */
  defaultOpen?: boolean;
  /** Whether to render in a portal (default: true) */
  modal?: boolean;
}

// =============================================================================
// DIALOG TRIGGER TYPES
// =============================================================================

/** Props for the DialogTrigger component */
export interface DialogTriggerProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Trigger element (button, etc.) */
  children: Children;
  /** Render as child element instead of button */
  asChild?: boolean;
}

// =============================================================================
// DIALOG CONTENT TYPES
// =============================================================================

/** Props for the DialogContent component */
export interface DialogContentProps extends HTMLAttributes<HTMLDivElement> {
  /** Dialog content */
  children: Children;
  /** Size variant of the dialog */
  size?: DialogSize;
  /** Whether to show the close button (default: true) */
  showCloseButton?: boolean;
  /** Custom close button aria-label */
  closeButtonLabel?: string;
  /** Callback when close button is clicked */
  onClose?: () => void;
  /** Additional CSS classes */
  className?: string;
  /** Whether to prevent closing on outside click */
  preventCloseOnOutsideClick?: boolean;
  /** Whether to prevent closing on escape key */
  preventCloseOnEscape?: boolean;
}

// =============================================================================
// DIALOG OVERLAY TYPES
// =============================================================================

/** Props for the DialogOverlay component */
export interface DialogOverlayProps extends HTMLAttributes<HTMLDivElement> {
  /** Additional CSS classes */
  className?: string;
}

// =============================================================================
// DIALOG HEADER TYPES
// =============================================================================

/** Props for the DialogHeader component */
export interface DialogHeaderProps {
  /** Header content */
  children: Children;
  /** Additional CSS classes */
  className?: string;
}

/** Props for the DialogTitle component */
export interface DialogTitleProps {
  /** Title text */
  children: Children;
  /** Additional CSS classes */
  className?: string;
}

/** Props for the DialogDescription component */
export interface DialogDescriptionProps {
  /** Description text */
  children: Children;
  /** Additional CSS classes */
  className?: string;
}

// =============================================================================
// DIALOG BODY & FOOTER TYPES
// =============================================================================

/** Props for the DialogBody component */
export interface DialogBodyProps {
  /** Body content */
  children: Children;
  /** Additional CSS classes */
  className?: string;
}

/** Props for the DialogFooter component */
export interface DialogFooterProps {
  /** Footer content (typically buttons) */
  children: Children;
  /** Additional CSS classes */
  className?: string;
}

// =============================================================================
// DIALOG CLOSE TYPES
// =============================================================================

/** Props for the DialogClose component */
export interface DialogCloseProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Close button content */
  children?: Children;
  /** Render as child element */
  asChild?: boolean;
}

// =============================================================================
// STYLE MAPPINGS
// =============================================================================

/** Size width mappings for dialog content */
export const DIALOG_SIZE_STYLES: Record<DialogSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-[90vw] h-[90vh]',
} as const;

/** Animation classes for dialog */
export const DIALOG_ANIMATIONS = {
  overlay: {
    enter: 'animate-in fade-in-0',
    exit: 'animate-out fade-out-0',
    base: 'duration-200',
  },
  content: {
    enter: 'animate-in fade-in-0 zoom-in-95 slide-in-from-bottom-2',
    exit: 'animate-out fade-out-0 zoom-out-95 slide-out-to-bottom-2',
    base: 'duration-200',
  },
} as const;
