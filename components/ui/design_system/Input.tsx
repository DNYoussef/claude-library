/**
 * Input Components
 *
 * Form input components with labels, icons, and error states.
 * Includes single-line Input and multi-line Textarea.
 *
 * @example
 * ```tsx
 * // Input with label and icon
 * <Input
 *   label="Email"
 *   leftIcon={<MailIcon />}
 *   placeholder="you@example.com"
 * />
 *
 * // Textarea with error
 * <Textarea
 *   label="Description"
 *   error="Description is required"
 * />
 * ```
 */

import { forwardRef, useId } from 'react';
import type { InputProps, TextareaProps } from './types';

// =============================================================================
// SHARED STYLES
// =============================================================================

/**
 * Base input styles shared between Input and Textarea.
 */
const baseInputStyles = [
  'w-full bg-surface-elevated/80 border rounded-xl px-3 py-2 text-text-primary shadow-sm',
  'placeholder:text-text-muted',
  'focus:outline-none focus:ring-2 focus:ring-accent-500/60 focus:border-accent-500/60',
  'disabled:opacity-50 disabled:cursor-not-allowed',
  'transition-colors transition-shadow',
].join(' ');

/**
 * Label styles for form inputs.
 */
const labelStyles = 'block text-sm font-medium text-text-secondary mb-1';

/**
 * Error message styles.
 */
const errorStyles = 'mt-1 text-sm text-error';

/**
 * Hint text styles.
 */
const hintStyles = 'mt-1 text-xs text-text-muted';

// =============================================================================
// INPUT COMPONENT
// =============================================================================

/**
 * Input - Single-line form input with label, icons, and error states.
 *
 * @param props - Input properties (extends HTMLInputElement attributes)
 * @param props.label - Label text above input
 * @param props.error - Error message (shows error state when present)
 * @param props.hint - Hint text below input (hidden when error is shown)
 * @param props.leftIcon - Icon on the left side of input
 * @param props.rightIcon - Icon on the right side of input
 * @param ref - Forwarded ref to the input element
 *
 * @example
 * ```tsx
 * // Basic input with label
 * <Input label="Username" placeholder="Enter username" />
 *
 * // Input with icons
 * <Input
 *   label="Search"
 *   leftIcon={<SearchIcon />}
 *   rightIcon={<ClearIcon />}
 *   placeholder="Search..."
 * />
 *
 * // Input with error state
 * <Input
 *   label="Email"
 *   type="email"
 *   value={email}
 *   error={emailError}
 *   onChange={(e) => setEmail(e.target.value)}
 * />
 *
 * // Input with hint
 * <Input
 *   label="Password"
 *   type="password"
 *   hint="Must be at least 8 characters"
 * />
 * ```
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, leftIcon, rightIcon, className = '', id, ...props }, ref) => {
    const generatedId = useId();
    const inputId = id || `input-${generatedId}`;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className={labelStyles}>
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={`
              ${baseInputStyles}
              ${leftIcon ? 'pl-10' : ''}
              ${rightIcon ? 'pr-10' : ''}
              ${error ? 'border-error focus:ring-error focus:border-error' : 'border-border-default/70'}
              ${className}
            `}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p id={`${inputId}-error`} className={errorStyles} role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={`${inputId}-hint`} className={hintStyles}>
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

// =============================================================================
// TEXTAREA COMPONENT
// =============================================================================

/**
 * Textarea - Multi-line text input with label and error states.
 *
 * @param props - Textarea properties (extends HTMLTextAreaElement attributes)
 * @param props.label - Label text above textarea
 * @param props.error - Error message (shows error state when present)
 * @param props.hint - Hint text below textarea (hidden when error is shown)
 * @param ref - Forwarded ref to the textarea element
 *
 * @example
 * ```tsx
 * // Basic textarea
 * <Textarea label="Description" placeholder="Enter description..." />
 *
 * // Textarea with rows
 * <Textarea
 *   label="Bio"
 *   rows={5}
 *   placeholder="Tell us about yourself"
 * />
 *
 * // Textarea with error
 * <Textarea
 *   label="Comments"
 *   error="Comments are required"
 *   value={comments}
 *   onChange={(e) => setComments(e.target.value)}
 * />
 * ```
 */
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, className = '', id, ...props }, ref) => {
    const generatedId = useId();
    const textareaId = id || `textarea-${generatedId}`;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={textareaId} className={labelStyles}>
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={`
            ${baseInputStyles}
            resize-y min-h-[100px]
            ${error ? 'border-error focus:ring-error focus:border-error' : 'border-border-default/70'}
            ${className}
          `}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${textareaId}-error` : hint ? `${textareaId}-hint` : undefined}
          {...props}
        />
        {error && (
          <p id={`${textareaId}-error`} className={errorStyles} role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={`${textareaId}-hint`} className={hintStyles}>
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
