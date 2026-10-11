import React from 'react';
import { cn } from '../../utils/cn';
import { REACTIONS } from '../../utils/constants';

/**
 * Universal Qualitative Reaction Badge.
 * Strictly non-numeric, text-based, zero emojis or star ratings.
 *
 * Reactions:
 * - Peak: Electric Gold
 * - Loved It: Warm Coral
 * - Good Time: Radiant Teal
 * - Not My Thing: Muted Lavender
 * - Skip: Crimson
 */
export function ReactionBadge({
  reactionKey,
  size = 'md',
  variant = 'pill',
  showDescription = false,
  className,
}) {
  if (!reactionKey) return null;

  // Normalize key (e.g. 'peak', 'PEAK', 'loved_it', 'loved-it')
  const normalizedKey = String(reactionKey).toLowerCase().replace(/-/g, '_');
  const config = Object.values(REACTIONS).find((r) => r.key === normalizedKey);

  if (!config) return null;

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[10px] tracking-wider font-semibold',
    sm: 'px-2 py-0.5 text-xs font-semibold tracking-wide',
    md: 'px-2.5 py-1 text-xs font-semibold tracking-wide',
    lg: 'px-4 py-1.5 text-sm font-bold tracking-wide',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border uppercase transition-colors',
        sizeClasses[size] || sizeClasses.md,
        config.badgeClass,
        className
      )}
      title={config.description}
      aria-label={`Reaction: ${config.label}`}
    >
      <span className="truncate">{config.label}</span>
      {showDescription && (
        <span className="hidden sm:inline lowercase text-text-secondary text-[11px] normal-case font-normal border-l border-border-neutral pl-2 ml-1">
          {config.description}
        </span>
      )}
    </span>
  );
}
