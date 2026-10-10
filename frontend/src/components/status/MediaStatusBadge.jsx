import React from 'react';
import { cn } from '../../utils/cn';
import { TRACKING_STATUSES } from '../../utils/constants';

/**
 * MediaStatusBadge — Visual badge for user tracking status.
 */
export function MediaStatusBadge({ status, size = 'sm', className }) {
  if (!status) return null;

  const config = TRACKING_STATUSES[status] || {
    key: status,
    label: status.replace(/_/g, ' '),
    badgeClass: 'text-text-secondary bg-surface-2 border-border-neutral',
  };

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[10px]',
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full border',
        sizeClasses[size] || sizeClasses.sm,
        config.badgeClass,
        className
      )}
    >
      {config.label}
    </span>
  );
}
