/**
 * Badge Components
 *
 * Status indicators and badges with semantic color variants.
 * Includes Badge for text labels and StatusDot for simple indicators.
 *
 * @example
 * ```tsx
 * // Badge with icon
 * <Badge variant="success" icon={<CheckIcon />}>Completed</Badge>
 *
 * // Status dot with pulse
 * <StatusDot status="success" pulse />
 * ```
 */

import type { BadgeProps, StatusDotProps, BadgeVariant, Size, Status } from './types';

// =============================================================================
// STYLE DEFINITIONS
// =============================================================================

/**
 * Variant styles for Badge component.
 * Uses opacity modifiers for background colors to maintain readability.
 */
const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-surface-elevated/70 text-text-secondary border-border-default/80',
  success: 'bg-success/15 text-success border-success/30',
  warning: 'bg-warning/15 text-warning border-warning/30',
  error: 'bg-error/15 text-error border-error/30',
  info: 'bg-info/15 text-info border-info/30',
  accent: 'bg-accent-500/15 text-accent-400 border-accent-500/30',
};

/**
 * Size styles for Badge component.
 */
const sizeStyles: Record<Size, string> = {
  sm: 'px-1.5 py-0.5 text-xs',
  md: 'px-2 py-1 text-xs',
  lg: 'px-3 py-1.5 text-sm',
};

/**
 * Color styles for StatusDot component.
 */
const dotColors: Record<Status, string> = {
  success: 'bg-success',
  warning: 'bg-warning',
  error: 'bg-error',
  info: 'bg-info',
  neutral: 'bg-text-muted',
};

/**
 * Size styles for StatusDot component.
 */
const dotSizes: Record<Size, string> = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-3 h-3',
};

// =============================================================================
// BADGE COMPONENT
// =============================================================================

/**
 * Badge - Status indicator badge with semantic color variants.
 *
 * @param props - Badge properties
 * @param props.children - Badge text content
 * @param props.variant - Visual variant: 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent'
 * @param props.size - Badge size: 'sm' | 'md' | 'lg'
 * @param props.icon - Optional leading icon
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * // Default badge
 * <Badge>Draft</Badge>
 *
 * // Success badge with icon
 * <Badge variant="success" icon={<CheckCircle size={12} />}>
 *   Published
 * </Badge>
 *
 * // Large error badge
 * <Badge variant="error" size="lg">Critical</Badge>
 * ```
 */
export function Badge({
  children,
  variant = 'default',
  size = 'md',
  icon,
  className = '',
}: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full font-medium border backdrop-blur-sm shadow-sm
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
    >
      {icon}
      {children}
    </span>
  );
}

// =============================================================================
// STATUS DOT COMPONENT
// =============================================================================

/**
 * StatusDot - Simple colored dot indicator for showing status.
 *
 * @param props - StatusDot properties
 * @param props.status - Status determines color: 'success' | 'warning' | 'error' | 'info' | 'neutral'
 * @param props.size - Dot size: 'sm' | 'md' | 'lg'
 * @param props.pulse - Whether to show pulse animation
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * // Basic status dot
 * <StatusDot status="success" />
 *
 * // Large pulsing dot for active state
 * <StatusDot status="info" size="lg" pulse />
 *
 * // Inline with text
 * <span className="flex items-center gap-2">
 *   <StatusDot status="success" />
 *   Online
 * </span>
 * ```
 */
export function StatusDot({
  status,
  size = 'md',
  pulse = false,
  className = '',
}: StatusDotProps) {
  return (
    <span
      className={`
        inline-block rounded-full
        ${dotColors[status]}
        ${dotSizes[size]}
        ${pulse ? 'animate-pulse' : ''}
        ${className}
      `}
      aria-label={`Status: ${status}`}
    />
  );
}
