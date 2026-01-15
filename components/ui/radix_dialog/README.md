# Radix Dialog Component

A pre-styled, accessible modal dialog built on Radix UI Dialog with Tailwind CSS theming support. Includes animations, overlay, close button, and full keyboard navigation.

## Installation

### Dependencies

```bash
npm install @radix-ui/react-dialog
# or
pnpm add @radix-ui/react-dialog
```

### Required Packages

- React 18+
- TypeScript 5+
- Tailwind CSS 3+
- @radix-ui/react-dialog 1.0+

### File Setup

Copy the `radix-dialog` directory to your project's components folder.

```
components/
  ui/
    radix-dialog/
      Dialog.tsx
      Dialog.css
      types.ts
      index.ts
      README.md
```

### CSS Import

Import the animation styles in your global CSS or component:

```css
/* In your global.css or app.css */
@import './components/ui/radix-dialog/Dialog.css';
```

Or import directly in your component:

```tsx
import './Dialog.css';
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
  --accent-400: #818cf8;
  --accent-500: #6366f1;
}
```

## Components

### Dialog

Root component that provides dialog state.

```tsx
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  DialogFooter,
  DialogClose,
} from './radix-dialog';

// Basic usage
<Dialog>
  <DialogTrigger>Open Dialog</DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
      <DialogDescription>Optional description text.</DialogDescription>
    </DialogHeader>
    <DialogBody>
      <p>Your content here</p>
    </DialogBody>
    <DialogFooter>
      <DialogClose>Cancel</DialogClose>
      <button className="btn-primary">Confirm</button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Controlled Dialog

```tsx
const [open, setOpen] = useState(false);

<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent>
    <DialogBody>Controlled dialog content</DialogBody>
  </DialogContent>
</Dialog>

// Open from elsewhere
<button onClick={() => setOpen(true)}>Open</button>
```

### Size Variants

```tsx
// Small dialog
<DialogContent size="sm">...</DialogContent>

// Medium (default)
<DialogContent size="md">...</DialogContent>

// Large
<DialogContent size="lg">...</DialogContent>

// Extra large
<DialogContent size="xl">...</DialogContent>

// Full screen (90vw x 90vh)
<DialogContent size="full">...</DialogContent>
```

### Custom Close Behavior

```tsx
// Hide the default close button
<DialogContent showCloseButton={false}>
  <DialogBody>No X button</DialogBody>
  <DialogFooter>
    <DialogClose>Close</DialogClose>
  </DialogFooter>
</DialogContent>

// Prevent accidental closing
<DialogContent
  preventCloseOnOutsideClick
  preventCloseOnEscape
>
  <DialogBody>Important form - must use buttons to close</DialogBody>
</DialogContent>

// Custom close callback
<DialogContent onClose={() => console.log('Dialog closed')}>
  ...
</DialogContent>
```

### As Child Pattern

```tsx
// Custom trigger button
<DialogTrigger asChild>
  <button className="custom-styles">Open</button>
</DialogTrigger>

// Custom close button
<DialogClose asChild>
  <button className="custom-styles">Close</button>
</DialogClose>
```

## Props Reference

### Dialog Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Dialog content |
| `open` | `boolean` | - | Controlled open state |
| `onOpenChange` | `(open: boolean) => void` | - | Open state change callback |
| `defaultOpen` | `boolean` | `false` | Default open state (uncontrolled) |
| `modal` | `boolean` | `true` | Whether dialog blocks interaction |

### DialogTrigger Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Trigger content |
| `asChild` | `boolean` | `false` | Render as child element |
| `className` | `string` | - | Additional CSS classes |

### DialogContent Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Content |
| `size` | `'sm' \| 'md' \| 'lg' \| 'xl' \| 'full'` | `'md'` | Size variant |
| `showCloseButton` | `boolean` | `true` | Show X close button |
| `closeButtonLabel` | `string` | `'Close dialog'` | Close button aria-label |
| `onClose` | `() => void` | - | Close callback |
| `preventCloseOnOutsideClick` | `boolean` | `false` | Block overlay click close |
| `preventCloseOnEscape` | `boolean` | `false` | Block Escape key close |
| `className` | `string` | - | Additional CSS classes |

### DialogHeader, DialogBody, DialogFooter Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Section content |
| `className` | `string` | - | Additional CSS classes |

### DialogTitle Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Title text |
| `className` | `string` | - | Additional CSS classes |

### DialogDescription Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Description text |
| `className` | `string` | - | Additional CSS classes |

### DialogClose Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | - | Button content |
| `asChild` | `boolean` | `false` | Render as child element |
| `className` | `string` | - | Additional CSS classes |

## Accessibility

This component follows WAI-ARIA Dialog Modal pattern:

- **Focus Management**: Focus is trapped within the dialog
- **Keyboard Navigation**:
  - `Tab` / `Shift+Tab` - Navigate focusable elements
  - `Escape` - Close dialog (unless prevented)
- **Screen Readers**:
  - Dialog is announced with title and description
  - Close button has aria-label
  - Modal role is properly set
- **Motion**: Respects `prefers-reduced-motion` preference

## Animations

The dialog includes smooth enter/exit animations:

- **Overlay**: Fade in/out with backdrop blur
- **Content**: Zoom and slide from bottom
- **Duration**: 200ms with eased timing

Disable animations in `Dialog.css` or via Tailwind config if needed.

## Mobile Support

- Full-width on screens < 640px
- Optional bottom-sheet style for very small screens
- Touch-friendly close button

## TypeScript

All types are exported for use in your components:

```tsx
import type {
  DialogSize,
  DialogProps,
  DialogTriggerProps,
  DialogContentProps,
  DialogHeaderProps,
  DialogTitleProps,
  DialogDescriptionProps,
  DialogBodyProps,
  DialogFooterProps,
  DialogCloseProps,
} from './radix-dialog';
```

## Theming

Uses CSS variables for consistent theming with the design system:

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
