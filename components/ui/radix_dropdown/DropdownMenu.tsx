/**
 * Radix Dropdown Menu Components
 *
 * Pre-styled Radix Dropdown Menu with Tailwind CSS.
 * Fully accessible with keyboard navigation, submenus, checkboxes, and radio groups.
 *
 * @example
 * ```tsx
 * <DropdownMenu>
 *   <DropdownMenuTrigger>Options</DropdownMenuTrigger>
 *   <DropdownMenuContent>
 *     <DropdownMenuLabel>Actions</DropdownMenuLabel>
 *     <DropdownMenuItem icon={<EditIcon />}>Edit</DropdownMenuItem>
 *     <DropdownMenuItem icon={<CopyIcon />} shortcut="Ctrl+C">Copy</DropdownMenuItem>
 *     <DropdownMenuSeparator />
 *     <DropdownMenuItem variant="destructive" icon={<TrashIcon />}>Delete</DropdownMenuItem>
 *   </DropdownMenuContent>
 * </DropdownMenu>
 * ```
 *
 * @packageDocumentation
 */

'use client';

import { forwardRef } from 'react';
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import {
  ITEM_VARIANT_STYLES,
  MENU_ANIMATIONS,
  type DropdownMenuProps,
  type DropdownMenuTriggerProps,
  type DropdownMenuContentProps,
  type DropdownMenuItemProps,
  type DropdownMenuCheckboxItemProps,
  type DropdownMenuRadioGroupProps,
  type DropdownMenuRadioItemProps,
  type DropdownMenuLabelProps,
  type DropdownMenuSeparatorProps,
  type DropdownMenuSubProps,
  type DropdownMenuSubTriggerProps,
  type DropdownMenuSubContentProps,
  type DropdownMenuGroupProps,
} from './types';

// =============================================================================
// DROPDOWN MENU ROOT
// =============================================================================

/**
 * DropdownMenu - Root component that provides menu state.
 *
 * @param props - Menu properties
 * @param props.children - Menu content (trigger and portal)
 * @param props.open - Controlled open state
 * @param props.onOpenChange - Callback when open state changes
 * @param props.defaultOpen - Default open state (uncontrolled)
 * @param props.modal - Whether menu is modal
 * @param props.dir - Reading direction for RTL
 *
 * @example
 * ```tsx
 * <DropdownMenu>
 *   <DropdownMenuTrigger>Menu</DropdownMenuTrigger>
 *   <DropdownMenuContent>
 *     <DropdownMenuItem>Item 1</DropdownMenuItem>
 *   </DropdownMenuContent>
 * </DropdownMenu>
 * ```
 */
export function DropdownMenu({
  children,
  open,
  onOpenChange,
  defaultOpen,
  modal = true,
  dir,
}: DropdownMenuProps) {
  return (
    <DropdownMenuPrimitive.Root
      open={open}
      onOpenChange={onOpenChange}
      defaultOpen={defaultOpen}
      modal={modal}
      dir={dir}
    >
      {children}
    </DropdownMenuPrimitive.Root>
  );
}

// =============================================================================
// DROPDOWN MENU TRIGGER
// =============================================================================

/**
 * DropdownMenuTrigger - Button that opens the dropdown menu.
 *
 * @param props - Trigger properties
 * @param props.children - Trigger content
 * @param props.asChild - Render as child element
 *
 * @example
 * ```tsx
 * <DropdownMenuTrigger>Open Menu</DropdownMenuTrigger>
 *
 * // As child (custom button)
 * <DropdownMenuTrigger asChild>
 *   <button className="icon-button"><MoreIcon /></button>
 * </DropdownMenuTrigger>
 * ```
 */
export const DropdownMenuTrigger = forwardRef<HTMLButtonElement, DropdownMenuTriggerProps>(
  ({ children, asChild = false, className = '', ...props }, ref) => (
    <DropdownMenuPrimitive.Trigger
      ref={ref}
      asChild={asChild}
      className={`
        inline-flex items-center justify-center rounded-lg px-3 py-2
        bg-surface-elevated text-text-primary border border-border-default
        hover:bg-surface-primary hover:border-border-subtle
        focus:outline-none focus:ring-2 focus:ring-accent-500 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-colors
        ${className}
      `}
      {...props}
    >
      {children}
    </DropdownMenuPrimitive.Trigger>
  )
);

DropdownMenuTrigger.displayName = 'DropdownMenuTrigger';

// =============================================================================
// DROPDOWN MENU CONTENT
// =============================================================================

/**
 * DropdownMenuContent - The dropdown menu container.
 *
 * @param props - Content properties
 * @param props.children - Menu items
 * @param props.align - Alignment: 'start' | 'center' | 'end'
 * @param props.side - Side: 'top' | 'right' | 'bottom' | 'left'
 * @param props.sideOffset - Offset from trigger in pixels
 * @param props.alignOffset - Alignment offset in pixels
 * @param props.className - Additional CSS classes
 * @param props.loop - Whether to loop focus
 *
 * @example
 * ```tsx
 * <DropdownMenuContent align="end" sideOffset={8}>
 *   <DropdownMenuItem>Item</DropdownMenuItem>
 * </DropdownMenuContent>
 * ```
 */
export const DropdownMenuContent = forwardRef<HTMLDivElement, DropdownMenuContentProps>(
  (
    {
      children,
      align = 'center',
      side = 'bottom',
      sideOffset = 4,
      alignOffset = 0,
      className = '',
      preventCloseOnOutsideClick = false,
      preventCloseOnEscape = false,
      collisionBoundary,
      collisionPadding = 8,
      loop = true,
      ...props
    },
    ref
  ) => (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.Content
        ref={ref}
        align={align}
        side={side}
        sideOffset={sideOffset}
        alignOffset={alignOffset}
        collisionBoundary={collisionBoundary}
        collisionPadding={collisionPadding}
        loop={loop}
        className={`
          z-50 min-w-[180px] overflow-hidden rounded-lg
          bg-surface-primary border border-border-default shadow-lg
          p-1
          data-[state=open]:${MENU_ANIMATIONS.content.enter}
          data-[state=closed]:${MENU_ANIMATIONS.content.exit}
          data-[side=top]:${MENU_ANIMATIONS.side.top}
          data-[side=right]:${MENU_ANIMATIONS.side.right}
          data-[side=bottom]:${MENU_ANIMATIONS.side.bottom}
          data-[side=left]:${MENU_ANIMATIONS.side.left}
          ${MENU_ANIMATIONS.content.base}
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
        {children}
      </DropdownMenuPrimitive.Content>
    </DropdownMenuPrimitive.Portal>
  )
);

DropdownMenuContent.displayName = 'DropdownMenuContent';

// =============================================================================
// DROPDOWN MENU ITEM
// =============================================================================

/**
 * DropdownMenuItem - A selectable menu item.
 *
 * @param props - Item properties
 * @param props.children - Item content
 * @param props.disabled - Whether item is disabled
 * @param props.variant - Visual variant: 'default' | 'destructive'
 * @param props.icon - Leading icon
 * @param props.shortcut - Keyboard shortcut display
 * @param props.onSelect - Callback when selected
 * @param props.preventClose - Prevent menu from closing on select
 *
 * @example
 * ```tsx
 * <DropdownMenuItem icon={<EditIcon />} shortcut="Ctrl+E">
 *   Edit
 * </DropdownMenuItem>
 *
 * <DropdownMenuItem variant="destructive" icon={<TrashIcon />}>
 *   Delete
 * </DropdownMenuItem>
 * ```
 */
export const DropdownMenuItem = forwardRef<HTMLDivElement, DropdownMenuItemProps>(
  (
    {
      children,
      disabled = false,
      variant = 'default',
      icon,
      shortcut,
      onSelect,
      className = '',
      preventClose = false,
      ...props
    },
    ref
  ) => (
    <DropdownMenuPrimitive.Item
      ref={ref}
      disabled={disabled}
      onSelect={(event) => {
        if (preventClose) {
          event.preventDefault();
        }
        onSelect?.(event);
      }}
      className={`
        relative flex items-center gap-2 px-2 py-1.5 rounded-md
        text-sm cursor-pointer select-none outline-none
        ${ITEM_VARIANT_STYLES[variant]}
        data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed
        transition-colors
        ${className}
      `}
      {...props}
    >
      {icon && <span className="flex-shrink-0 w-4 h-4">{icon}</span>}
      <span className="flex-grow">{children}</span>
      {shortcut && (
        <span className="ml-auto text-xs text-text-muted">{shortcut}</span>
      )}
    </DropdownMenuPrimitive.Item>
  )
);

DropdownMenuItem.displayName = 'DropdownMenuItem';

// =============================================================================
// DROPDOWN MENU CHECKBOX ITEM
// =============================================================================

/**
 * DropdownMenuCheckboxItem - A checkbox menu item.
 *
 * @param props - Checkbox item properties
 * @param props.children - Item content
 * @param props.checked - Checked state
 * @param props.onCheckedChange - Callback when checked changes
 * @param props.disabled - Whether item is disabled
 *
 * @example
 * ```tsx
 * const [checked, setChecked] = useState(false);
 *
 * <DropdownMenuCheckboxItem checked={checked} onCheckedChange={setChecked}>
 *   Show hidden files
 * </DropdownMenuCheckboxItem>
 * ```
 */
export const DropdownMenuCheckboxItem = forwardRef<HTMLDivElement, DropdownMenuCheckboxItemProps>(
  ({ children, checked, onCheckedChange, disabled = false, className = '', ...props }, ref) => (
    <DropdownMenuPrimitive.CheckboxItem
      ref={ref}
      checked={checked}
      onCheckedChange={onCheckedChange}
      disabled={disabled}
      className={`
        relative flex items-center gap-2 px-2 py-1.5 pl-8 rounded-md
        text-sm text-text-primary cursor-pointer select-none outline-none
        focus:bg-surface-elevated
        data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed
        transition-colors
        ${className}
      `}
      {...props}
    >
      <span className="absolute left-2 flex h-4 w-4 items-center justify-center">
        <DropdownMenuPrimitive.ItemIndicator>
          <CheckIcon className="h-4 w-4" />
        </DropdownMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </DropdownMenuPrimitive.CheckboxItem>
  )
);

DropdownMenuCheckboxItem.displayName = 'DropdownMenuCheckboxItem';

// =============================================================================
// DROPDOWN MENU RADIO GROUP
// =============================================================================

/**
 * DropdownMenuRadioGroup - Container for radio items.
 *
 * @param props - Radio group properties
 * @param props.children - Radio items
 * @param props.value - Current selected value
 * @param props.onValueChange - Callback when value changes
 *
 * @example
 * ```tsx
 * const [size, setSize] = useState('medium');
 *
 * <DropdownMenuRadioGroup value={size} onValueChange={setSize}>
 *   <DropdownMenuRadioItem value="small">Small</DropdownMenuRadioItem>
 *   <DropdownMenuRadioItem value="medium">Medium</DropdownMenuRadioItem>
 *   <DropdownMenuRadioItem value="large">Large</DropdownMenuRadioItem>
 * </DropdownMenuRadioGroup>
 * ```
 */
export function DropdownMenuRadioGroup({
  children,
  value,
  onValueChange,
}: DropdownMenuRadioGroupProps) {
  return (
    <DropdownMenuPrimitive.RadioGroup value={value} onValueChange={onValueChange}>
      {children}
    </DropdownMenuPrimitive.RadioGroup>
  );
}

// =============================================================================
// DROPDOWN MENU RADIO ITEM
// =============================================================================

/**
 * DropdownMenuRadioItem - A radio menu item.
 *
 * @param props - Radio item properties
 * @param props.children - Item content
 * @param props.value - Item value
 * @param props.disabled - Whether item is disabled
 */
export const DropdownMenuRadioItem = forwardRef<HTMLDivElement, DropdownMenuRadioItemProps>(
  ({ children, value, disabled = false, className = '', ...props }, ref) => (
    <DropdownMenuPrimitive.RadioItem
      ref={ref}
      value={value}
      disabled={disabled}
      className={`
        relative flex items-center gap-2 px-2 py-1.5 pl-8 rounded-md
        text-sm text-text-primary cursor-pointer select-none outline-none
        focus:bg-surface-elevated
        data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed
        transition-colors
        ${className}
      `}
      {...props}
    >
      <span className="absolute left-2 flex h-4 w-4 items-center justify-center">
        <DropdownMenuPrimitive.ItemIndicator>
          <DotIcon className="h-2 w-2 fill-current" />
        </DropdownMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </DropdownMenuPrimitive.RadioItem>
  )
);

DropdownMenuRadioItem.displayName = 'DropdownMenuRadioItem';

// =============================================================================
// DROPDOWN MENU LABEL
// =============================================================================

/**
 * DropdownMenuLabel - A non-interactive label for grouping items.
 *
 * @param props - Label properties
 * @param props.children - Label text
 * @param props.inset - Whether to inset for icon alignment
 *
 * @example
 * ```tsx
 * <DropdownMenuLabel>Account</DropdownMenuLabel>
 * <DropdownMenuItem>Profile</DropdownMenuItem>
 * <DropdownMenuItem>Settings</DropdownMenuItem>
 * ```
 */
export function DropdownMenuLabel({
  children,
  inset = false,
  className = '',
}: DropdownMenuLabelProps) {
  return (
    <DropdownMenuPrimitive.Label
      className={`
        px-2 py-1.5 text-xs font-semibold text-text-muted
        ${inset ? 'pl-8' : ''}
        ${className}
      `}
    >
      {children}
    </DropdownMenuPrimitive.Label>
  );
}

// =============================================================================
// DROPDOWN MENU SEPARATOR
// =============================================================================

/**
 * DropdownMenuSeparator - A visual divider between menu items.
 *
 * @example
 * ```tsx
 * <DropdownMenuItem>Item 1</DropdownMenuItem>
 * <DropdownMenuSeparator />
 * <DropdownMenuItem>Item 2</DropdownMenuItem>
 * ```
 */
export function DropdownMenuSeparator({ className = '' }: DropdownMenuSeparatorProps) {
  return (
    <DropdownMenuPrimitive.Separator
      className={`-mx-1 my-1 h-px bg-border-subtle ${className}`}
    />
  );
}

// =============================================================================
// DROPDOWN MENU SUB
// =============================================================================

/**
 * DropdownMenuSub - Container for a submenu.
 *
 * @param props - Submenu properties
 * @param props.children - Submenu trigger and content
 * @param props.open - Controlled open state
 * @param props.onOpenChange - Callback when open changes
 * @param props.defaultOpen - Default open state
 *
 * @example
 * ```tsx
 * <DropdownMenuSub>
 *   <DropdownMenuSubTrigger icon={<ShareIcon />}>Share</DropdownMenuSubTrigger>
 *   <DropdownMenuSubContent>
 *     <DropdownMenuItem>Email</DropdownMenuItem>
 *     <DropdownMenuItem>Twitter</DropdownMenuItem>
 *   </DropdownMenuSubContent>
 * </DropdownMenuSub>
 * ```
 */
export function DropdownMenuSub({
  children,
  open,
  onOpenChange,
  defaultOpen,
}: DropdownMenuSubProps) {
  return (
    <DropdownMenuPrimitive.Sub
      open={open}
      onOpenChange={onOpenChange}
      defaultOpen={defaultOpen}
    >
      {children}
    </DropdownMenuPrimitive.Sub>
  );
}

// =============================================================================
// DROPDOWN MENU SUB TRIGGER
// =============================================================================

/**
 * DropdownMenuSubTrigger - Trigger for opening a submenu.
 *
 * @param props - Sub trigger properties
 * @param props.children - Trigger content
 * @param props.disabled - Whether trigger is disabled
 * @param props.icon - Leading icon
 */
export const DropdownMenuSubTrigger = forwardRef<HTMLDivElement, DropdownMenuSubTriggerProps>(
  ({ children, disabled = false, icon, className = '', ...props }, ref) => (
    <DropdownMenuPrimitive.SubTrigger
      ref={ref}
      disabled={disabled}
      className={`
        relative flex items-center gap-2 px-2 py-1.5 rounded-md
        text-sm text-text-primary cursor-pointer select-none outline-none
        focus:bg-surface-elevated
        data-[state=open]:bg-surface-elevated
        data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed
        transition-colors
        ${className}
      `}
      {...props}
    >
      {icon && <span className="flex-shrink-0 w-4 h-4">{icon}</span>}
      <span className="flex-grow">{children}</span>
      <ChevronRightIcon className="ml-auto h-4 w-4" />
    </DropdownMenuPrimitive.SubTrigger>
  )
);

DropdownMenuSubTrigger.displayName = 'DropdownMenuSubTrigger';

// =============================================================================
// DROPDOWN MENU SUB CONTENT
// =============================================================================

/**
 * DropdownMenuSubContent - Content container for a submenu.
 *
 * @param props - Sub content properties
 * @param props.children - Submenu items
 * @param props.alignOffset - Alignment offset
 * @param props.sideOffset - Side offset
 * @param props.loop - Whether to loop focus
 */
export const DropdownMenuSubContent = forwardRef<HTMLDivElement, DropdownMenuSubContentProps>(
  ({ children, alignOffset = -4, sideOffset = 2, className = '', loop = true, ...props }, ref) => (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.SubContent
        ref={ref}
        alignOffset={alignOffset}
        sideOffset={sideOffset}
        loop={loop}
        className={`
          z-50 min-w-[180px] overflow-hidden rounded-lg
          bg-surface-primary border border-border-default shadow-lg
          p-1
          data-[state=open]:${MENU_ANIMATIONS.content.enter}
          data-[state=closed]:${MENU_ANIMATIONS.content.exit}
          data-[side=top]:${MENU_ANIMATIONS.side.top}
          data-[side=right]:${MENU_ANIMATIONS.side.right}
          data-[side=bottom]:${MENU_ANIMATIONS.side.bottom}
          data-[side=left]:${MENU_ANIMATIONS.side.left}
          ${MENU_ANIMATIONS.content.base}
          ${className}
        `}
        {...props}
      >
        {children}
      </DropdownMenuPrimitive.SubContent>
    </DropdownMenuPrimitive.Portal>
  )
);

DropdownMenuSubContent.displayName = 'DropdownMenuSubContent';

// =============================================================================
// DROPDOWN MENU GROUP
// =============================================================================

/**
 * DropdownMenuGroup - Groups related menu items together.
 *
 * @param props - Group properties
 * @param props.children - Group content
 *
 * @example
 * ```tsx
 * <DropdownMenuGroup>
 *   <DropdownMenuLabel>Account</DropdownMenuLabel>
 *   <DropdownMenuItem>Profile</DropdownMenuItem>
 *   <DropdownMenuItem>Settings</DropdownMenuItem>
 * </DropdownMenuGroup>
 * ```
 */
export function DropdownMenuGroup({ children }: DropdownMenuGroupProps) {
  return <DropdownMenuPrimitive.Group>{children}</DropdownMenuPrimitive.Group>;
}

// =============================================================================
// ICONS
// =============================================================================

/** Check icon for checkbox items */
function CheckIcon({ className = '' }: { className?: string }) {
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
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

/** Dot icon for radio items */
function DotIcon({ className = '' }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      className={className}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="6" fill="currentColor" />
    </svg>
  );
}

/** Chevron right icon for submenu triggers */
function ChevronRightIcon({ className = '' }: { className?: string }) {
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
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}
