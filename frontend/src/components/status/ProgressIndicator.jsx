import React from 'react';
import { cn } from '../../utils/cn';

/**
 * ProgressIndicator — Displays category-specific progress counters and visual bars.
 *
 * Examples:
 * - TV: S2 E5 (or 14/24 eps)
 * - Manga: Ch. 142
 * - Game: 34.5 hrs
 */
export function ProgressIndicator({
  category,
  current,
  total,
  label,
  showBar = true,
  className,
}) {
  const hasValues = current !== undefined && current !== null;
  if (!hasValues && !label) return null;

  const percentage =
    total && total > 0 && current ? Math.min(Math.round((current / total) * 100), 100) : null;

  let displayLabel = label;
  if (!displayLabel && hasValues) {
    if (category === 'SERIES') {
      displayLabel = total ? `Ep ${current} of ${total}` : `Ep ${current}`;
    } else if (category === 'MANGA' || category === 'MANHWA') {
      displayLabel = total ? `Ch ${current} of ${total}` : `Ch ${current}`;
    } else if (category === 'GAME') {
      displayLabel = `${current} hrs`;
    } else {
      displayLabel = total ? `${current} / ${total}` : `${current}`;
    }
  }

  return (
    <div className={cn('flex flex-col gap-1 w-full', className)}>
      <div className="flex items-center justify-between text-xs text-text-secondary">
        <span className="font-medium text-text-primary">{displayLabel}</span>
        {percentage !== null && <span>{percentage}%</span>}
      </div>
      {showBar && percentage !== null && (
        <div className="w-full h-1.5 rounded-full bg-surface-2 overflow-hidden border border-border-subtle">
          <div
            className="h-full bg-teal transition-all duration-300 rounded-full"
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </div>
  );
}
