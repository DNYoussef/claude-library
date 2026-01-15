/**
 * Card Components
 *
 * A set of composable card components for building card-based UIs.
 * Supports multiple variants and interactive states.
 *
 * @example
 * ```tsx
 * <Card variant="elevated" padding="lg">
 *   <CardHeader title="Dashboard" subtitle="Overview" action={<Button>Edit</Button>} />
 *   <CardContent>Main content goes here</CardContent>
 *   <CardFooter>
 *     <Button>Cancel</Button>
 *     <Button variant="primary">Save</Button>
 *   </CardFooter>
 * </Card>
 * ```
 */

import type { KeyboardEvent } from 'react';
import type { CardProps, CardHeaderProps, CardSectionProps, CardVariant, Padding } from './types';

// Type for extended Card props including toggle state
interface CardComponentProps extends CardProps {
  /** Whether the card is in a pressed/selected state (for toggle buttons) */
  isPressed?: boolean;
}

// =============================================================================
// STYLE DEFINITIONS
// =============================================================================

/**
 * Variant styles for the Card component.
 * Uses CSS variables for theming support.
 */
const variantStyles: Record<CardVariant, string> = {
  default: 'bg-surface-primary border border-border-subtle shadow-sm',
  elevated: [
    'bg-gradient-to-br from-surface-elevated to-surface-primary',
    'border border-border-default shadow-lg',
  ].join(' '),
  outlined: 'bg-transparent border border-border-default/80',
  interactive: [
    'bg-surface-primary border border-border-subtle shadow-sm',
    'hover:border-accent-500/50 hover:shadow-lg hover:-translate-y-0.5',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-500/60 focus-visible:ring-offset-0',
    'cursor-pointer transition-all',
  ].join(' '),
};

/**
 * Padding styles for the Card component.
 */
const paddingStyles: Record<Padding, string> = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
};

// =============================================================================
// CARD COMPONENT
// =============================================================================

/**
 * Card - Base card component with multiple variants.
 *
 * @param props - Card properties
 * @param props.children - Card content
 * @param props.className - Additional CSS classes
 * @param props.variant - Visual variant: 'default' | 'elevated' | 'outlined' | 'interactive'
 * @param props.onClick - Optional click handler (makes card interactive)
 * @param props.padding - Internal padding: 'none' | 'sm' | 'md' | 'lg'
 *
 * @example
 * ```tsx
 * // Default card
 * <Card>Content</Card>
 *
 * // Elevated card with large padding
 * <Card variant="elevated" padding="lg">Content</Card>
 *
 * // Interactive card with click handler
 * <Card variant="interactive" onClick={() => navigate('/details')}>
 *   Click me
 * </Card>
 *
 * // Toggle card with pressed state
 * <Card variant="interactive" onClick={toggle} isPressed={isSelected}>
 *   Selectable item
 * </Card>
 * ```
 */
export function Card({
  children,
  className = '',
  variant = 'default',
  onClick,
  padding = 'md',
  isPressed,
}: CardComponentProps) {
  const isInteractive = variant === 'interactive' || !!onClick;

  const handleKeyDown = (e: KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className={`rounded-xl ${variantStyles[variant]} ${paddingStyles[padding]} ${className}`}
      onClick={onClick}
      onKeyDown={isInteractive ? handleKeyDown : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      role={isInteractive ? 'button' : undefined}
      aria-pressed={isInteractive && isPressed !== undefined ? isPressed : undefined}
    >
      {children}
    </div>
  );
}

// =============================================================================
// CARD HEADER COMPONENT
// =============================================================================

/**
 * CardHeader - Header section for cards with title, subtitle, and action slot.
 *
 * @param props - CardHeader properties
 * @param props.title - Main header title
 * @param props.subtitle - Optional subtitle text
 * @param props.action - Optional action element (button, menu, etc.)
 *
 * @example
 * ```tsx
 * <CardHeader
 *   title="User Settings"
 *   subtitle="Manage your account"
 *   action={<IconButton icon={<SettingsIcon />} />}
 * />
 * ```
 */
export function CardHeader({ title, subtitle, action }: CardHeaderProps) {
  return (
    <div className="flex justify-between items-start mb-3">
      <div>
        <h3 className="font-medium text-text-primary">{title}</h3>
        {subtitle && <p className="text-sm text-text-secondary">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

// =============================================================================
// CARD CONTENT COMPONENT
// =============================================================================

/**
 * CardContent - Main content section for cards.
 *
 * @param props - CardContent properties
 * @param props.children - Content to display
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * <CardContent>
 *   <p>This is the main content of the card.</p>
 * </CardContent>
 * ```
 */
export function CardContent({ children, className = '' }: CardSectionProps) {
  return <div className={`text-sm text-text-secondary ${className}`}>{children}</div>;
}

// =============================================================================
// CARD FOOTER COMPONENT
// =============================================================================

/**
 * CardFooter - Footer section for cards, typically used for actions.
 * Includes a top border separator and flex layout for buttons.
 *
 * @param props - CardFooter properties
 * @param props.children - Footer content (typically buttons)
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * <CardFooter>
 *   <Button variant="ghost">Cancel</Button>
 *   <Button variant="primary">Confirm</Button>
 * </CardFooter>
 * ```
 */
export function CardFooter({ children, className = '' }: CardSectionProps) {
  return (
    <div className={`flex gap-2 mt-4 pt-4 border-t border-border-subtle ${className}`}>
      {children}
    </div>
  );
}
