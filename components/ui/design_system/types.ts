/**
 * Design System - Shared Types and Variants
 *
 * This file contains all shared TypeScript types and variant definitions
 * used across the design system components.
 *
 * @packageDocumentation
 */

import type { InputHTMLAttributes, TextareaHTMLAttributes } from 'react';

/** Generic children type for components */
type Children = React.ReactNode;

// =============================================================================
// COMMON TYPES
// =============================================================================

/** Standard size options used across components */
export type Size = 'sm' | 'md' | 'lg';

/** Padding options for components */
export type Padding = 'none' | 'sm' | 'md' | 'lg';

/** Semantic status values */
export type Status = 'success' | 'warning' | 'error' | 'info' | 'neutral';

/** Trend direction for metrics */
export type TrendDirection = 'up' | 'down' | 'neutral';

// =============================================================================
// CARD TYPES
// =============================================================================

/** Card visual variants */
export type CardVariant = 'default' | 'elevated' | 'outlined' | 'interactive';

/** Props for the Card component */
export interface CardProps {
  /** Card content */
  children: Children;
  /** Additional CSS classes */
  className?: string;
  /** Visual variant of the card */
  variant?: CardVariant;
  /** Click handler - automatically makes card interactive */
  onClick?: () => void;
  /** Internal padding */
  padding?: Padding;
}

/** Props for the CardHeader component */
export interface CardHeaderProps {
  /** Header title text */
  title: string;
  /** Optional subtitle text */
  subtitle?: string;
  /** Optional action element (button, icon, etc.) */
  action?: Children;
}

/** Props for CardContent and CardFooter */
export interface CardSectionProps {
  /** Section content */
  children: Children;
  /** Additional CSS classes */
  className?: string;
}

// =============================================================================
// BADGE TYPES
// =============================================================================

/** Badge visual variants */
export type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent';

/** Props for the Badge component */
export interface BadgeProps {
  /** Badge content */
  children: Children;
  /** Visual variant */
  variant?: BadgeVariant;
  /** Size of the badge */
  size?: Size;
  /** Optional leading icon */
  icon?: Children;
  /** Additional CSS classes */
  className?: string;
}

/** Props for the StatusDot component */
export interface StatusDotProps {
  /** Status determines the color */
  status: Status;
  /** Size of the dot */
  size?: Size;
  /** Whether to show pulse animation */
  pulse?: boolean;
  /** Additional CSS classes */
  className?: string;
}

// =============================================================================
// INPUT TYPES
// =============================================================================

/** Props for the Input component */
export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Label text above input */
  label?: string;
  /** Error message (shows error state when present) */
  error?: string;
  /** Hint text below input */
  hint?: string;
  /** Icon on the left side */
  leftIcon?: Children;
  /** Icon on the right side */
  rightIcon?: Children;
}

/** Props for the Textarea component */
export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Label text above textarea */
  label?: string;
  /** Error message (shows error state when present) */
  error?: string;
  /** Hint text below textarea */
  hint?: string;
}

// =============================================================================
// METRIC TYPES
// =============================================================================

/** Metric card visual variants */
export type MetricVariant = 'default' | 'accent' | 'success' | 'warning' | 'error';

/** Trend indicator data */
export interface TrendData {
  /** Percentage value */
  value: number;
  /** Direction of the trend */
  direction: TrendDirection;
}

/** Props for the MetricCard component */
export interface MetricCardProps {
  /** Metric title/label */
  title: string;
  /** Metric value (formatted as string or number) */
  value: string | number;
  /** Optional subtitle/description */
  subtitle?: string;
  /** Optional leading icon */
  icon?: Children;
  /** Optional trend indicator */
  trend?: TrendData;
  /** Visual variant */
  variant?: MetricVariant;
  /** Additional CSS classes */
  className?: string;
}

/** Props for the MetricGrid layout component */
export interface MetricGridProps {
  /** MetricCard children */
  children: Children;
  /** Number of columns */
  columns?: 2 | 3 | 4;
  /** Additional CSS classes */
  className?: string;
}

// =============================================================================
// STYLE MAPPINGS
// =============================================================================

/**
 * CSS variable-based color tokens.
 * These map to CSS custom properties that should be defined in your theme.
 *
 * Required CSS variables:
 * --surface-primary, --surface-elevated
 * --border-subtle, --border-default
 * --text-primary, --text-secondary, --text-muted
 * --accent-400, --accent-500
 * --success, --warning, --error, --info
 */
export const CSS_TOKENS = {
  surfaces: {
    primary: 'bg-surface-primary',
    elevated: 'bg-surface-elevated',
  },
  borders: {
    subtle: 'border-border-subtle',
    default: 'border-border-default',
  },
  text: {
    primary: 'text-text-primary',
    secondary: 'text-text-secondary',
    muted: 'text-text-muted',
  },
  semantic: {
    success: 'text-success',
    warning: 'text-warning',
    error: 'text-error',
    info: 'text-info',
    accent: 'text-accent-400',
  },
} as const;
