import React from 'react';
import { cn } from '../../utils/cn';
import { LoadingSpinner } from '../feedback/LoadingSpinner';

/**
 * DreamTeal Button primitive.
 */
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon: Icon,
  className,
  type = 'button',
  ...props
}) {
  const variantClasses = {
    primary:
      'bg-teal hover:bg-teal-glow text-white shadow-sm hover:shadow-glow border border-teal-light/20',
    secondary:
      'bg-surface-2 hover:bg-surface-3 text-text-primary border border-border-neutral hover:border-border-neutral/90',
    ghost:
      'bg-transparent hover:bg-surface-2 text-text-secondary hover:text-text-primary border border-transparent',
    danger:
      'bg-red-950/60 hover:bg-red-900/80 text-red-100 border border-red-700/60',
  };

  const sizeClasses = {
    sm: 'px-2.5 py-1 text-xs gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-5 py-2.5 text-base gap-2.5',
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 focus-ring',
        sizeClasses[size] || sizeClasses.md,
        variantClasses[variant] || variantClasses.primary,
        (disabled || loading) && 'opacity-50 cursor-not-allowed',
        className
      )}
      {...props}
    >
      {loading ? (
        <LoadingSpinner size="sm" />
      ) : (
        Icon && <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
      )}
      <span>{children}</span>
    </button>
  );
}
