# Radix Dropdown Menu Component

A pre-styled, accessible dropdown menu built on Radix UI Dropdown Menu with Tailwind CSS theming. Includes menu items, checkboxes, radio groups, separators, submenus, and full keyboard navigation.

## Installation

### Dependencies

```bash
npm install @radix-ui/react-dropdown-menu
# or
pnpm add @radix-ui/react-dropdown-menu
```

### Required Packages

- React 18+
- TypeScript 5+
- Tailwind CSS 3+
- @radix-ui/react-dropdown-menu 2.0+

### File Setup

Copy the `radix-dropdown` directory to your project's components folder.

```
components/
  ui/
    radix-dropdown/
      DropdownMenu.tsx
      types.ts
      index.ts
      README.md
```

### Required CSS Variables

Add these CSS custom properties to your global styles (same as design-system):

```css
:root {
  /* Surfaces */
  --surface-primary: #1a1a2e;
  --surface-elevated: #252542;

  /* Borders */
  --border-subtle: #2a2a4a;
  --border-default: #3a3a5a;

  /* Text */
  --text-primary: #ffffff;
  --text-secondary: #a0a0b0;
  --text-muted: #606070;

  /* Accent */
  --accent-500: #6366f1;

  /* Semantic */
  --error: #ef4444;
}
```

## Components

### Basic Dropdown Menu

```tsx
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from './radix-dropdown';

<DropdownMenu>
  <DropdownMenuTrigger>Options</DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>Actions</DropdownMenuLabel>
    <DropdownMenuItem>Edit</DropdownMenuItem>
    <DropdownMenuItem>Duplicate</DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem variant="destructive">Delete</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### Menu Items with Icons and Shortcuts

```tsx
import { Edit, Copy, Trash2 } from 'lucide-react';

<DropdownMenuContent>
  <DropdownMenuItem icon={<Edit size={16} />} shortcut="Ctrl+E">
    Edit
  </DropdownMenuItem>
  <DropdownMenuItem icon={<Copy size={16} />} shortcut="Ctrl+C">
    Copy
  </DropdownMenuItem>
  <DropdownMenuSeparator />
  <DropdownMenuItem variant="destructive" icon={<Trash2 size={16} />}>
    Delete
  </DropdownMenuItem>
</DropdownMenuContent>
```

### Checkbox Items

```tsx
import { useState } from 'react';

const [showHidden, setShowHidden] = useState(false);
const [showPreview, setShowPreview] = useState(true);

<DropdownMenuContent>
  <DropdownMenuLabel>View Options</DropdownMenuLabel>
  <DropdownMenuCheckboxItem
    checked={showHidden}
    onCheckedChange={setShowHidden}
  >
    Show hidden files
  </DropdownMenuCheckboxItem>
  <DropdownMenuCheckboxItem
    checked={showPreview}
    onCheckedChange={setShowPreview}
  >
    Show preview pane
  </DropdownMenuCheckboxItem>
</DropdownMenuContent>
```

### Radio Groups

```tsx
import { useState } from 'react';

const [sortBy, setSortBy] = useState('name');

<DropdownMenuContent>
  <DropdownMenuLabel>Sort By</DropdownMenuLabel>
  <DropdownMenuRadioGroup value={sortBy} onValueChange={setSortBy}>
    <DropdownMenuRadioItem value="name">Name</DropdownMenuRadioItem>
    <DropdownMenuRadioItem value="date">Date Modified</DropdownMenuRadioItem>
    <DropdownMenuRadioItem value="size">Size</DropdownMenuRadioItem>
  </DropdownMenuRadioGroup>
</DropdownMenuContent>
```

### Submenus

```tsx
<DropdownMenuContent>
  <DropdownMenuItem>New File</DropdownMenuItem>
  <DropdownMenuSub>
    <DropdownMenuSubTrigger icon={<Share size={16} />}>
      Share
    </DropdownMenuSubTrigger>
    <DropdownMenuSubContent>
      <DropdownMenuItem>Email</DropdownMenuItem>
      <DropdownMenuItem>Twitter</DropdownMenuItem>
      <DropdownMenuItem>LinkedIn</DropdownMenuItem>
    </DropdownMenuSubContent>
  </DropdownMenuSub>
  <DropdownMenuSeparator />
  <DropdownMenuItem>Download</DropdownMenuItem>
</DropdownMenuContent>
```

### Grouped Items

```tsx
<DropdownMenuContent>
  <DropdownMenuGroup>
    <DropdownMenuLabel>Account</DropdownMenuLabel>
    <DropdownMenuItem>Profile</DropdownMenuItem>
    <DropdownMenuItem>Settings</DropdownMenuItem>
    <DropdownMenuItem>Billing</DropdownMenuItem>
  </DropdownMenuGroup>
  <DropdownMenuSeparator />
  <DropdownMenuGroup>
    <DropdownMenuLabel>Help</DropdownMenuLabel>
    <DropdownMenuItem>Documentation</DropdownMenuItem>
    <DropdownMenuItem>Support</DropdownMenuItem>
  </DropdownMenuGroup>
</DropdownMenuContent>
```

### Position and Alignment

```tsx
// Align to end (right side)
<DropdownMenuContent align="end">...</DropdownMenuContent>

// Appear above trigger
<DropdownMenuContent side="top">...</DropdownMenuContent>

// Custom offset
<DropdownMenuContent sideOffset={8} alignOffset={4}>...</DropdownMenuContent>
```

### Controlled Menu

```tsx
const [open, setOpen] = useState(false);

<DropdownMenu open={open} onOpenChange={setOpen}>
  <DropdownMenuTrigger>Menu</DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuItem onSelect={() => console.log('Selected')}>
      Item
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>

// Open from elsewhere
<button onClick={() => setOpen(true)}>Open Menu</button>
```

### As Child Pattern

```tsx
// Custom trigger
<DropdownMenuTrigger asChild>
  <button className="icon-button">
    <MoreHorizontal />
  </button>
</DropdownMenuTrigger>
```

### Prevent Close on Select

```tsx
// Keep menu open after selection
<DropdownMenuItem preventClose onSelect={() => doSomething()}>
  Toggle Option
</DropdownMenuItem>
```

## Props Reference

### DropdownMenu Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Menu content |
| `open` | `boolean` | - | Controlled open state |
| `onOpenChange` | `(open: boolean) => void` | - | Open state callback |
| `defaultOpen` | `boolean` | `false` | Default open state |
| `modal` | `boolean` | `true` | Whether menu is modal |
| `dir` | `'ltr' \| 'rtl'` | - | Reading direction |

### DropdownMenuTrigger Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Trigger content |
| `asChild` | `boolean` | `false` | Render as child element |
| `className` | `string` | - | Additional CSS classes |

### DropdownMenuContent Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Menu items |
| `align` | `'start' \| 'center' \| 'end'` | `'center'` | Horizontal alignment |
| `side` | `'top' \| 'right' \| 'bottom' \| 'left'` | `'bottom'` | Position side |
| `sideOffset` | `number` | `4` | Offset from trigger |
| `alignOffset` | `number` | `0` | Alignment offset |
| `loop` | `boolean` | `true` | Loop focus navigation |
| `className` | `string` | - | Additional CSS classes |

### DropdownMenuItem Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Item content |
| `disabled` | `boolean` | `false` | Whether disabled |
| `variant` | `'default' \| 'destructive'` | `'default'` | Visual variant |
| `icon` | `ReactNode` | - | Leading icon |
| `shortcut` | `string` | - | Keyboard shortcut text |
| `onSelect` | `(event: Event) => void` | - | Selection callback |
| `preventClose` | `boolean` | `false` | Keep menu open |
| `className` | `string` | - | Additional CSS classes |

### DropdownMenuCheckboxItem Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Item content |
| `checked` | `boolean` | - | Checked state |
| `onCheckedChange` | `(checked: boolean) => void` | - | Change callback |
| `disabled` | `boolean` | `false` | Whether disabled |
| `className` | `string` | - | Additional CSS classes |

### DropdownMenuRadioGroup Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Radio items |
| `value` | `string` | - | Current value |
| `onValueChange` | `(value: string) => void` | - | Value change callback |

### DropdownMenuRadioItem Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Item content |
| `value` | `string` | - | Item value |
| `disabled` | `boolean` | `false` | Whether disabled |
| `className` | `string` | - | Additional CSS classes |

### DropdownMenuLabel Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Label text |
| `inset` | `boolean` | `false` | Inset for icon alignment |
| `className` | `string` | - | Additional CSS classes |

### DropdownMenuSubTrigger Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Trigger content |
| `disabled` | `boolean` | `false` | Whether disabled |
| `icon` | `ReactNode` | - | Leading icon |
| `className` | `string` | - | Additional CSS classes |

## Accessibility

This component follows WAI-ARIA Menu pattern:

- **Focus Management**: Focus is properly managed within menu
- **Keyboard Navigation**:
  - `Enter` / `Space` - Select item
  - `ArrowDown` / `ArrowUp` - Navigate items
  - `ArrowRight` - Open submenu
  - `ArrowLeft` - Close submenu
  - `Escape` - Close menu
  - `Home` / `End` - Jump to first/last item
  - Type to search - Jump to matching item
- **Screen Readers**:
  - Menu role is properly set
  - Items are announced with state (checked, expanded)
  - Disabled items are announced
- **Motion**: Respects `prefers-reduced-motion`

## Animations

The menu includes smooth animations using Tailwind CSS:

- **Content**: Fade + zoom + slide based on side
- **Duration**: 150ms with eased timing
- **Exit**: Reverse animations on close

Add these to your Tailwind config for animations:

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      keyframes: {
        'slide-in-from-top': {
          from: { transform: 'translateY(-0.5rem)' },
          to: { transform: 'translateY(0)' },
        },
        // ... other animations
      },
    },
  },
};
```

Or use `tailwindcss-animate` plugin for pre-built animations.

## TypeScript

All types are exported:

```tsx
import type {
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
} from './radix-dropdown';
```

## Theming

Uses CSS variables for consistent theming:

```css
/* Light theme override */
[data-theme="light"] {
  --surface-primary: #ffffff;
  --surface-elevated: #f8fafc;
  --text-primary: #1e293b;
  --border-default: #e2e8f0;
}
```

## Source

LEGO component created for Life-OS ecosystem.

---

**Version:** 1.0.0
**Last Updated:** 2026-01-10
