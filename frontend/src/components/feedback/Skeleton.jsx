import React from 'react';
import { cn } from '../../utils/cn';

/**
 * Reusable pulse skeleton block with dark surface tones.
 */
export function Skeleton({ className, ...props }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'animate-pulse rounded bg-surface-2 border border-border-subtle/50',
        className
      )}
      {...props}
    />
  );
}
