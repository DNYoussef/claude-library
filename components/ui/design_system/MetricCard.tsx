/**
 * Metric Card Components
 *
 * Components for displaying key metrics with optional trend indicators.
 * Includes MetricCard for individual metrics and MetricGrid for layouts.
 *
 * @example
 * ```tsx
 * <MetricGrid columns={4}>
 *   <MetricCard title="Revenue" value="$45,231" trend={{ value: 12, direction: 'up' }} />
 *   <MetricCard title="Users" value={1234} variant="accent" />
 *   <MetricCard title="Errors" value={3} variant="error" />
 *   <MetricCard title="Uptime" value="99.9%" variant="success" />
 * </MetricGrid>
 * ```
 */

import type { MetricCardProps, MetricGridProps, MetricVariant, TrendDirection } from './types';

// =============================================================================
// STYLE DEFINITIONS
// =============================================================================

/**
 * Border color styles based on variant.
 */
const variantStyles: Record<MetricVariant, string> = {
  default: 'border-border-subtle/70',
  accent: 'border-accent-500/40',
  success: 'border-success/40',
  warning: 'border-warning/40',
  error: 'border-error/40',
};

/**
 * Value text color styles based on variant.
 */
const valueVariantStyles: Record<MetricVariant, string> = {
  default: 'text-text-primary',
  accent: 'text-accent-400',
  success: 'text-success',
  warning: 'text-warning',
  error: 'text-error',
};

/**
 * Trend indicator colors based on direction.
 */
const trendColors: Record<TrendDirection, string> = {
  up: 'text-success',
  down: 'text-error',
  neutral: 'text-text-muted',
};

/**
 * Grid column configurations.
 */
const columnStyles: Record<2 | 3 | 4, string> = {
  2: 'grid-cols-2',
  3: 'grid-cols-3',
  4: 'grid-cols-4',
};

// =============================================================================
// METRIC CARD COMPONENT
// =============================================================================

/**
 * MetricCard - Display a key metric with optional trend indicator.
 *
 * @param props - MetricCard properties
 * @param props.title - Metric label/title
 * @param props.value - Metric value (string or number, numbers are auto-formatted)
 * @param props.subtitle - Optional description text
 * @param props.icon - Optional leading icon
 * @param props.trend - Optional trend indicator with value and direction
 * @param props.variant - Visual variant: 'default' | 'accent' | 'success' | 'warning' | 'error'
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * // Basic metric
 * <MetricCard title="Total Users" value={1234} />
 *
 * // Metric with trend
 * <MetricCard
 *   title="Revenue"
 *   value="$45,231"
 *   trend={{ value: 12.5, direction: 'up' }}
 *   subtitle="vs. last month"
 * />
 *
 * // Metric with icon and variant
 * <MetricCard
 *   title="Active Sessions"
 *   value={42}
 *   icon={<UsersIcon size={16} />}
 *   variant="accent"
 * />
 *
 * // Error metric
 * <MetricCard
 *   title="Failed Requests"
 *   value={7}
 *   variant="error"
 *   trend={{ value: 3, direction: 'up' }}
 * />
 * ```
 */
export function MetricCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant = 'default',
  className = '',
}: MetricCardProps) {
  // Format numeric values with locale-aware separators
  const formattedValue = typeof value === 'number' ? value.toLocaleString() : value;

  // Determine trend prefix based on direction
  const trendPrefix = trend
    ? trend.direction === 'up' ? '+'
    : trend.direction === 'down' ? '-'
    : ''
    : '';

  return (
    <div
      className={`
        bg-gradient-to-br from-surface-primary via-surface-primary to-surface-elevated
        border rounded-xl p-5 shadow-sm
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {/* Header with icon and title */}
      <div className="flex items-center gap-2 text-text-muted text-sm mb-1">
        {icon}
        <span>{title}</span>
      </div>

      {/* Value and trend */}
      <div className="flex items-end gap-2">
        <span className={`text-2xl font-bold ${valueVariantStyles[variant]}`}>
          {formattedValue}
        </span>
        {trend && (
          <span className={`text-sm font-medium ${trendColors[trend.direction]}`}>
            {trendPrefix}{Math.abs(trend.value)}%
          </span>
        )}
      </div>

      {/* Subtitle */}
      {subtitle && <p className="text-xs text-text-muted mt-1">{subtitle}</p>}
    </div>
  );
}

// =============================================================================
// METRIC GRID COMPONENT
// =============================================================================

/**
 * MetricGrid - Responsive grid layout for MetricCard components.
 *
 * @param props - MetricGrid properties
 * @param props.children - MetricCard components
 * @param props.columns - Number of columns: 2 | 3 | 4
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * // 4-column grid (default)
 * <MetricGrid>
 *   <MetricCard title="Users" value={1234} />
 *   <MetricCard title="Sessions" value={5678} />
 *   <MetricCard title="Bounce" value="32%" />
 *   <MetricCard title="Duration" value="4:32" />
 * </MetricGrid>
 *
 * // 3-column grid
 * <MetricGrid columns={3}>
 *   <MetricCard title="CPU" value="45%" />
 *   <MetricCard title="Memory" value="72%" />
 *   <MetricCard title="Disk" value="23%" />
 * </MetricGrid>
 *
 * // 2-column grid with custom gap
 * <MetricGrid columns={2} className="gap-6">
 *   <MetricCard title="Revenue" value="$45K" />
 *   <MetricCard title="Expenses" value="$32K" />
 * </MetricGrid>
 * ```
 */
export function MetricGrid({ children, columns = 4, className = '' }: MetricGridProps) {
  return (
    <div className={`grid gap-4 ${columnStyles[columns]} ${className}`}>
      {children}
    </div>
  );
}
