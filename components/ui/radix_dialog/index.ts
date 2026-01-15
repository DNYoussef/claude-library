/**
 * Radix Dialog - Component Exports
 *
 * Central export file for all Radix Dialog components and types.
 *
 * @example
 * ```tsx
 * import {
 *   Dialog,
 *   DialogTrigger,
 *   DialogContent,
 *   DialogHeader,
 *   DialogTitle,
 *   DialogDescription,
 *   DialogBody,
 *   DialogFooter,
 *   DialogClose,
 * } from './radix-dialog';
 * import type { DialogProps, DialogSize } from './radix-dialog';
 * ```
 *
 * @packageDocumentation
 */

// =============================================================================
// COMPONENT EXPORTS
// =============================================================================

export {
  Dialog,
  DialogTrigger,
  DialogOverlay,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  DialogFooter,
  DialogClose,
} from './Dialog';

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export type {
  DialogSize,
  DialogProps,
  DialogTriggerProps,
  DialogContentProps,
  DialogOverlayProps,
  DialogHeaderProps,
  DialogTitleProps,
  DialogDescriptionProps,
  DialogBodyProps,
  DialogFooterProps,
  DialogCloseProps,
} from './types';

// =============================================================================
// CONSTANT EXPORTS
// =============================================================================

export { DIALOG_SIZE_STYLES, DIALOG_ANIMATIONS } from './types';
