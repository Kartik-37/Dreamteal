import React from 'react';
import { cn } from '../../utils/cn';

/**
 * Polished loading spinner with DreamTeal teal accent.
 */
export function LoadingSpinner({ size = 'md', className, label = 'Loading...' }) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-2',
    lg: 'w-12 h-12 border-3',
  };

  return (
    <div
      role="status"
      aria-label={label}
      className={cn('inline-flex flex-col items-center justify-center gap-3', className)}
    >
      <div
        className={cn(
          'rounded-full border-border-neutral border-t-teal animate-spin',
          sizeClasses[size] || sizeClasses.md
        )}
      />
      {label && <span className="sr-only">{label}</span>}
    </div>
  );
}
