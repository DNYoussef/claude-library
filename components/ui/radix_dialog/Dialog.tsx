/**
 * Radix Dialog Components
 *
 * Pre-styled Radix Dialog with Tailwind CSS and animations.
 * Fully accessible modal dialog with overlay, close button, and keyboard navigation.
 *
 * @example
 * ```tsx
 * <Dialog>
 *   <DialogTrigger>Open Dialog</DialogTrigger>
 *   <DialogContent>
 *     <DialogHeader>
 *       <DialogTitle>Confirm Action</DialogTitle>
 *       <DialogDescription>This action cannot be undone.</DialogDescription>
 *     </DialogHeader>
 *     <DialogBody>
 *       <p>Are you sure you want to proceed?</p>
 *     </DialogBody>
 *     <DialogFooter>
 *       <DialogClose>Cancel</DialogClose>
 *       <button className="btn-primary">Confirm</button>
 *     </DialogFooter>
 *   </DialogContent>
 * </Dialog>
 * ```
 *
 * @packageDocumentation
 */

'use client';

import { forwardRef, createContext, useContext } from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import {
  DIALOG_SIZE_STYLES,
  DIALOG_ANIMATIONS,
  type DialogProps,
  type DialogTriggerProps,
  type DialogContentProps,
  type DialogOverlayProps,
  type DialogHeaderProps,
  type DialogTitleProps,
  type DialogDescriptionProps,
  type DialogBodyProps,
  type DialogFooterProps,
  type DialogCloseProps,
  type DialogSize,
} from './types';

// =============================================================================
// CONTEXT
// =============================================================================

interface DialogContextValue {
  size: DialogSize;
}

const DialogContext = createContext<DialogContextValue>({ size: 'md' });

// =============================================================================
// DIALOG ROOT
// =============================================================================

/**
 * Dialog - Root component that provides dialog state.
 *
 * @param props - Dialog properties
 * @param props.children - Dialog content (trigger and portal)
 * @param props.open - Controlled open state
 * @param props.onOpenChange - Callback when open state changes
 * @param props.defaultOpen - Default open state (uncontrolled)
 * @param props.modal - Whether dialog is modal (default: true)
 *
 * @example
 * ```tsx
 * // Uncontrolled
 * <Dialog>
 *   <DialogTrigger>Open</DialogTrigger>
 *   <DialogContent>Content</DialogContent>
 * </Dialog>
 *
 * // Controlled
 * const [open, setOpen] = useState(false);
 * <Dialog open={open} onOpenChange={setOpen}>
 *   <DialogContent>Content</DialogContent>
 * </Dialog>
 * ```
 */
export function Dialog({
  children,
  open,
  onOpenChange,
  defaultOpen,
  modal = true,
}: DialogProps) {
  return (
    <DialogPrimitive.Root
      open={open}
      onOpenChange={onOpenChange}
      defaultOpen={defaultOpen}
      modal={modal}
    >
      {children}
    </DialogPrimitive.Root>
  );
}

// =============================================================================
// DIALOG TRIGGER
// =============================================================================

/**
 * DialogTrigger - Button that opens the dialog.
 *
 * @param props - Trigger properties
 * @param props.children - Trigger content
 * @param props.asChild - Render as child element instead of button
 *
 * @example
 * ```tsx
 * <DialogTrigger>Open Dialog</DialogTrigger>
 *
 * // As child (custom button)
 * <DialogTrigger asChild>
 *   <button className="custom-button">Open</button>
 * </DialogTrigger>
 * ```
 */
export const DialogTrigger = forwardRef<HTMLButtonElement, DialogTriggerProps>(
  ({ children, asChild = false, className = '', ...props }, ref) => (
    <DialogPrimitive.Trigger
      ref={ref}
      asChild={asChild}
      className={`
        inline-flex items-center justify-center rounded-lg px-4 py-2
        bg-accent-500 text-white font-medium
        hover:bg-accent-400 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-colors
        ${className}
      `}
      {...props}
    >
      {children}
    </DialogPrimitive.Trigger>
  )
);

DialogTrigger.displayName = 'DialogTrigger';

// =============================================================================
// DIALOG OVERLAY
// =============================================================================

/**
 * DialogOverlay - Semi-transparent backdrop behind the dialog.
 *
 * @param props - Overlay properties
 * @param props.className - Additional CSS classes
 */
export const DialogOverlay = forwardRef<HTMLDivElement, DialogOverlayProps>(
  ({ className = '', ...props }, ref) => (
    <DialogPrimitive.Overlay
      ref={ref}
      className={`
        fixed inset-0 z-50 bg-black/50 backdrop-blur-sm
        data-[state=open]:${DIALOG_ANIMATIONS.overlay.enter}
        data-[state=closed]:${DIALOG_ANIMATIONS.overlay.exit}
        ${DIALOG_ANIMATIONS.overlay.base}
        ${className}
      `}
      {...props}
    />
  )
);

DialogOverlay.displayName = 'DialogOverlay';

// =============================================================================
// DIALOG CONTENT
// =============================================================================

/**
 * DialogContent - The main dialog container with overlay and close button.
 *
 * @param props - Content properties
 * @param props.children - Dialog content
 * @param props.size - Size variant: 'sm' | 'md' | 'lg' | 'xl' | 'full'
 * @param props.showCloseButton - Whether to show close button (default: true)
 * @param props.closeButtonLabel - Aria-label for close button
 * @param props.onClose - Callback when close button is clicked
 * @param props.className - Additional CSS classes
 * @param props.preventCloseOnOutsideClick - Prevent closing on overlay click
 * @param props.preventCloseOnEscape - Prevent closing on Escape key
 *
 * @example
 * ```tsx
 * // Default size
 * <DialogContent>Content</DialogContent>
 *
 * // Large with no close button
 * <DialogContent size="lg" showCloseButton={false}>
 *   Content
 * </DialogContent>
 *
 * // Prevent accidental closing
 * <DialogContent preventCloseOnOutsideClick preventCloseOnEscape>
 *   Important form
 * </DialogContent>
 * ```
 */
export const DialogContent = forwardRef<HTMLDivElement, DialogContentProps>(
  (
    {
      children,
      size = 'md',
      showCloseButton = true,
      closeButtonLabel = 'Close dialog',
      onClose,
      className = '',
      preventCloseOnOutsideClick = false,
      preventCloseOnEscape = false,
      ...props
    },
    ref
  ) => (
    <DialogPrimitive.Portal>
      <DialogOverlay />
      <DialogPrimitive.Content
        ref={ref}
        className={`
          fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2
          w-full ${DIALOG_SIZE_STYLES[size]}
          bg-surface-primary border border-border-default rounded-xl shadow-xl
          data-[state=open]:${DIALOG_ANIMATIONS.content.enter}
          data-[state=closed]:${DIALOG_ANIMATIONS.content.exit}
          ${DIALOG_ANIMATIONS.content.base}
          focus:outline-none
          ${className}
        `}
        onPointerDownOutside={(e) => {
          if (preventCloseOnOutsideClick) {
            e.preventDefault();
          }
        }}
        onEscapeKeyDown={(e) => {
          if (preventCloseOnEscape) {
            e.preventDefault();
          }
        }}
        {...props}
      >
        <DialogContext.Provider value={{ size }}>
          {children}
          {showCloseButton && (
            <DialogPrimitive.Close
              className={`
                absolute right-4 top-4 rounded-full p-1.5
                text-text-muted hover:text-text-primary hover:bg-surface-elevated
                focus:outline-none focus:ring-2 focus:ring-accent-500
                transition-colors
              `}
              aria-label={closeButtonLabel}
              onClick={onClose}
            >
              <CloseIcon className="h-4 w-4" />
            </DialogPrimitive.Close>
          )}
        </DialogContext.Provider>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  )
);

DialogContent.displayName = 'DialogContent';

// =============================================================================
// DIALOG HEADER
// =============================================================================

/**
 * DialogHeader - Container for title and description.
 *
 * @param props - Header properties
 * @param props.children - Header content (typically DialogTitle and DialogDescription)
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * <DialogHeader>
 *   <DialogTitle>Edit Profile</DialogTitle>
 *   <DialogDescription>Make changes to your profile here.</DialogDescription>
 * </DialogHeader>
 * ```
 */
export function DialogHeader({ children, className = '' }: DialogHeaderProps) {
  return (
    <div className={`px-6 pt-6 pb-4 ${className}`}>
      {children}
    </div>
  );
}

// =============================================================================
// DIALOG TITLE
// =============================================================================

/**
 * DialogTitle - Accessible title for the dialog.
 *
 * @param props - Title properties
 * @param props.children - Title text
 * @param props.className - Additional CSS classes
 */
export const DialogTitle = forwardRef<HTMLHeadingElement, DialogTitleProps>(
  ({ children, className = '', ...props }, ref) => (
    <DialogPrimitive.Title
      ref={ref}
      className={`text-lg font-semibold text-text-primary ${className}`}
      {...props}
    >
      {children}
    </DialogPrimitive.Title>
  )
);

DialogTitle.displayName = 'DialogTitle';

// =============================================================================
// DIALOG DESCRIPTION
// =============================================================================

/**
 * DialogDescription - Accessible description for the dialog.
 *
 * @param props - Description properties
 * @param props.children - Description text
 * @param props.className - Additional CSS classes
 */
export const DialogDescription = forwardRef<HTMLParagraphElement, DialogDescriptionProps>(
  ({ children, className = '', ...props }, ref) => (
    <DialogPrimitive.Description
      ref={ref}
      className={`text-sm text-text-secondary mt-1 ${className}`}
      {...props}
    >
      {children}
    </DialogPrimitive.Description>
  )
);

DialogDescription.displayName = 'DialogDescription';

// =============================================================================
// DIALOG BODY
// =============================================================================

/**
 * DialogBody - Main content area of the dialog.
 *
 * @param props - Body properties
 * @param props.children - Body content
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * <DialogBody>
 *   <form>
 *     <Input label="Name" />
 *     <Input label="Email" />
 *   </form>
 * </DialogBody>
 * ```
 */
export function DialogBody({ children, className = '' }: DialogBodyProps) {
  return (
    <div className={`px-6 py-4 ${className}`}>
      {children}
    </div>
  );
}

// =============================================================================
// DIALOG FOOTER
// =============================================================================

/**
 * DialogFooter - Footer with action buttons.
 *
 * @param props - Footer properties
 * @param props.children - Footer content (typically buttons)
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * <DialogFooter>
 *   <DialogClose>Cancel</DialogClose>
 *   <button className="btn-primary">Save</button>
 * </DialogFooter>
 * ```
 */
export function DialogFooter({ children, className = '' }: DialogFooterProps) {
  return (
    <div
      className={`
        px-6 py-4 border-t border-border-subtle
        flex justify-end gap-3
        ${className}
      `}
    >
      {children}
    </div>
  );
}

// =============================================================================
// DIALOG CLOSE
// =============================================================================

/**
 * DialogClose - Button that closes the dialog.
 *
 * @param props - Close button properties
 * @param props.children - Button content
 * @param props.asChild - Render as child element
 *
 * @example
 * ```tsx
 * // Default button
 * <DialogClose>Cancel</DialogClose>
 *
 * // As child (custom button)
 * <DialogClose asChild>
 *   <button className="custom-button">Close</button>
 * </DialogClose>
 * ```
 */
export const DialogClose = forwardRef<HTMLButtonElement, DialogCloseProps>(
  ({ children, asChild = false, className = '', ...props }, ref) => (
    <DialogPrimitive.Close
      ref={ref}
      asChild={asChild}
      className={`
        inline-flex items-center justify-center rounded-lg px-4 py-2
        bg-surface-elevated text-text-secondary font-medium border border-border-default
        hover:bg-surface-primary hover:text-text-primary
        focus:outline-none focus:ring-2 focus:ring-accent-500 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-colors
        ${className}
      `}
      {...props}
    >
      {children}
    </DialogPrimitive.Close>
  )
);

DialogClose.displayName = 'DialogClose';

// =============================================================================
// ICONS
// =============================================================================

/** Close icon (X) for the close button */
function CloseIcon({ className = '' }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
