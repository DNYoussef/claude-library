/**
 * Design System - Component Exports
 *
 * Central export file for all design system components and types.
 *
 * @example
 * ```tsx
 * import { Card, CardHeader, Badge, Input, MetricCard } from './design-system';
 * import type { BadgeVariant, MetricCardProps } from './design-system';
 * ```
 *
 * @packageDocumentation
 */

// =============================================================================
// COMPONENT EXPORTS
// =============================================================================

// Card components
export { Card, CardHeader, CardContent, CardFooter } from './Card';

// Badge components
export { Badge, StatusDot } from './Badge';

// Input components
export { Input, Textarea } from './Input';

// Metric components
export { MetricCard, MetricGrid } from './MetricCard';

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export type {
  // Common types
  Size,
  Padding,
  Status,
  TrendDirection,

  // Card types
  CardVariant,
  CardProps,
  CardHeaderProps,
  CardSectionProps,

  // Badge types
  BadgeVariant,
  BadgeProps,
  StatusDotProps,

  // Input types
  InputProps,
  TextareaProps,

  // Metric types
  MetricVariant,
  TrendData,
  MetricCardProps,
  MetricGridProps,
} from './types';

// Value exports (constants)
export { CSS_TOKENS } from './types';
