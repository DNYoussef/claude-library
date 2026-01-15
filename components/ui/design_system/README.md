# Design System UI Components

A reusable set of UI components extracted from Life-OS Frontend. Built with React, TypeScript, and Tailwind CSS with CSS variable theming support.

## Installation

Copy the `design-system` directory to your project's components folder.

### Dependencies

- React 18+
- TypeScript 5+
- Tailwind CSS 3+

### Required CSS Variables

Add these CSS custom properties to your global styles or Tailwind config:

```css
:root {
  /* SolarArcana theme tokens */
  /* See theme.css for the canonical palette */
}
```

Or import the shared theme file:

```css
@import "./design_system/theme.css";
```

If you prefer manual tokens, use this baseline:

```css
:root {
  /* Surfaces */
  --surface-primary: hsl(168 30% 10%);
  --surface-elevated: hsl(168 32% 12%);

  /* Borders */
  --border-subtle: hsl(170 22% 20%);
  --border-default: hsl(170 24% 24%);

  /* Text */
  --text-primary: hsl(60 20% 96%);
  --text-secondary: hsl(155 15% 70%);
  --text-muted: hsl(155 12% 55%);

  /* Accent */
  --accent-400: hsl(145 70% 45%);
  --accent-500: hsl(45 90% 55%);

  /* Semantic */
  --success: hsl(145 70% 45%);
  --warning: hsl(40 90% 55%);
  --error: hsl(0 75% 55%);
  --info: hsl(195 80% 50%);
}
```

### Tailwind Configuration

Extend your `tailwind.config.js`:

```js
module.exports = {
  theme: {
    extend: {
      colors: {
        surface: {
          primary: 'var(--surface-primary)',
          elevated: 'var(--surface-elevated)',
        },
        border: {
          subtle: 'var(--border-subtle)',
          default: 'var(--border-default)',
        },
        text: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
        },
        accent: {
          400: 'var(--accent-400)',
          500: 'var(--accent-500)',
        },
        success: 'var(--success)',
        warning: 'var(--warning)',
        error: 'var(--error)',
        info: 'var(--info)',
      },
    },
  },
};
```

## Components

### Card

Container component with multiple variants for content grouping.

```tsx
import { Card, CardHeader, CardContent, CardFooter } from './design-system';

// Basic card
<Card>Content here</Card>

// Elevated card with sections
<Card variant="elevated" padding="lg">
  <CardHeader
    title="Dashboard"
    subtitle="Overview"
    action={<Button>Edit</Button>}
  />
  <CardContent>Main content</CardContent>
  <CardFooter>
    <Button>Cancel</Button>
    <Button variant="primary">Save</Button>
  </CardFooter>
</Card>

// Interactive card
<Card variant="interactive" onClick={() => navigate('/details')}>
  Click me
</Card>
```

**Card Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'default' \| 'elevated' \| 'outlined' \| 'interactive'` | `'default'` | Visual variant |
| `padding` | `'none' \| 'sm' \| 'md' \| 'lg'` | `'md'` | Internal padding |
| `onClick` | `() => void` | - | Click handler (makes card interactive) |
| `className` | `string` | - | Additional CSS classes |

### Badge

Status indicator badges with semantic colors.

```tsx
import { Badge, StatusDot } from './design-system';

// Text badge
<Badge variant="success">Completed</Badge>

// Badge with icon
<Badge variant="warning" icon={<AlertIcon />} size="lg">
  Pending Review
</Badge>

// Status dot
<StatusDot status="success" pulse />
```

**Badge Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'default' \| 'success' \| 'warning' \| 'error' \| 'info' \| 'accent'` | `'default'` | Color variant |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Badge size |
| `icon` | `ReactNode` | - | Leading icon |
| `className` | `string` | - | Additional CSS classes |

**StatusDot Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `status` | `'success' \| 'warning' \| 'error' \| 'info' \| 'neutral'` | - | Status color |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Dot size |
| `pulse` | `boolean` | `false` | Pulse animation |

### Input

Form inputs with labels, icons, and error states.

```tsx
import { Input, Textarea } from './design-system';

// Input with label and icons
<Input
  label="Email"
  leftIcon={<MailIcon />}
  placeholder="you@example.com"
  hint="We'll never share your email"
/>

// Input with error
<Input
  label="Password"
  type="password"
  error="Password must be at least 8 characters"
/>

// Textarea
<Textarea
  label="Description"
  rows={5}
  placeholder="Enter description..."
/>
```

**Input Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Label text |
| `error` | `string` | - | Error message |
| `hint` | `string` | - | Hint text |
| `leftIcon` | `ReactNode` | - | Left icon |
| `rightIcon` | `ReactNode` | - | Right icon |
| ...rest | `InputHTMLAttributes` | - | Native input props |

**Textarea Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Label text |
| `error` | `string` | - | Error message |
| `hint` | `string` | - | Hint text |
| ...rest | `TextareaHTMLAttributes` | - | Native textarea props |

### MetricCard

Display key metrics with optional trend indicators.

```tsx
import { MetricCard, MetricGrid } from './design-system';

// Single metric
<MetricCard
  title="Revenue"
  value="$45,231"
  icon={<DollarIcon />}
  trend={{ value: 12.5, direction: 'up' }}
  subtitle="vs. last month"
/>

// Metric grid
<MetricGrid columns={4}>
  <MetricCard title="Users" value={1234} />
  <MetricCard title="Sessions" value={5678} variant="accent" />
  <MetricCard title="Errors" value={3} variant="error" />
  <MetricCard title="Uptime" value="99.9%" variant="success" />
</MetricGrid>
```

**MetricCard Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | - | Metric label |
| `value` | `string \| number` | - | Metric value |
| `subtitle` | `string` | - | Description text |
| `icon` | `ReactNode` | - | Leading icon |
| `trend` | `{ value: number, direction: 'up' \| 'down' \| 'neutral' }` | - | Trend indicator |
| `variant` | `'default' \| 'accent' \| 'success' \| 'warning' \| 'error'` | `'default'` | Color variant |
| `className` | `string` | - | Additional CSS classes |

**MetricGrid Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `columns` | `2 \| 3 \| 4` | `4` | Number of columns |
| `className` | `string` | - | Additional CSS classes |

## TypeScript Types

All types are exported from the main index file:

```tsx
import type {
  // Common
  Size,
  Padding,
  Status,
  TrendDirection,

  // Card
  CardVariant,
  CardProps,
  CardHeaderProps,
  CardSectionProps,

  // Badge
  BadgeVariant,
  BadgeProps,
  StatusDotProps,

  // Input
  InputProps,
  TextareaProps,

  // Metric
  MetricVariant,
  TrendData,
  MetricCardProps,
  MetricGridProps,
} from './design-system';
```

## Theming

All components use CSS variables for colors, making theming straightforward:

```css
/* Light theme */
:root {
  --surface-primary: #ffffff;
  --surface-elevated: #f8fafc;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  /* ... */
}

/* Dark theme */
[data-theme="dark"] {
  --surface-primary: #1a1a2e;
  --surface-elevated: #252542;
  --text-primary: #ffffff;
  --text-secondary: #a0a0b0;
  /* ... */
}
```

## Accessibility

- All interactive elements support keyboard navigation
- Form inputs include proper ARIA attributes
- Error states are announced to screen readers
- Status indicators include aria-labels
- Focus states are visible and consistent

## Source

Extracted from: `D:\Projects\life-os-frontend\src\components\ui\`

---

**Version:** 1.0.0
**Last Updated:** 2026-01-10
