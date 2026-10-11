import React from 'react';
import { Film } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * Editorial Empty State presentation with dark surface styling.
 */
export function EmptyState({
  title = 'No items found',
  description = 'There is nothing here to display right now.',
  icon: Icon = Film,
  action,
  className,
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-12 text-center rounded-xl bg-surface-1/40 border border-border-neutral/60 backdrop-blur-sm',
        className
      )}
    >
      <div className="w-14 h-14 rounded-full bg-surface-2 flex items-center justify-center mb-4 text-text-secondary border border-border-neutral">
        <Icon className="w-7 h-7" aria-hidden="true" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary tracking-tight mb-2">
        {title}
      </h3>
      <p className="text-sm text-text-secondary max-w-md mb-6 leading-relaxed">
        {description}
      </p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
