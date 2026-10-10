import React from 'react';
import { cn } from '../../utils/cn';
import { REACTION_LIST } from '../../utils/constants';

/**
 * ReactionSelector — Interactive qualitative verdict picker.
 *
 * Strictly non-numeric, text-based labels only. Zero emojis, zero stars.
 * Controlled component: does not perform unsolicited backend mutations.
 */
export function ReactionSelector({
  value,
  onChange,
  disabled = false,
  size = 'md',
  className,
}) {
  const normalizedValue = value ? String(value).toLowerCase().replace(/-/g, '_') : null;

  return (
    <div
      role="radiogroup"
      aria-label="Select qualitative reaction"
      className={cn('inline-flex flex-wrap items-center gap-2', className)}
    >
      {REACTION_LIST.map((reaction) => {
        const isSelected = normalizedValue === reaction.key;

        return (
          <button
            key={reaction.key}
            type="button"
            role="radio"
            aria-checked={isSelected}
            aria-label={`${reaction.label}: ${reaction.description}`}
            disabled={disabled}
            onClick={() => {
              if (!disabled && onChange) {
                // Toggle off if already selected, or select new
                onChange(isSelected ? null : reaction.key);
              }
            }}
            className={cn(
              'group relative inline-flex items-center justify-center rounded-lg border font-medium uppercase tracking-wider text-xs transition-all duration-200 focus-ring',
              size === 'sm' ? 'px-2.5 py-1 text-[11px]' : 'px-3.5 py-1.5 text-xs',
              isSelected
                ? `${reaction.badgeClass} ring-2 ring-offset-2 ring-offset-background-deep shadow-sm`
                : 'border-border-neutral bg-surface-1 text-text-secondary hover:text-text-primary hover:border-border-neutral/80 hover:bg-surface-2',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            style={{
              borderColor: isSelected ? reaction.color : undefined,
              color: isSelected ? reaction.color : undefined,
              backgroundColor: isSelected ? reaction.bg : undefined,
              '--tw-ring-color': isSelected ? reaction.color : undefined,
            }}
          >
            <span>{reaction.label}</span>
          </button>
        );
      })}
    </div>
  );
}
