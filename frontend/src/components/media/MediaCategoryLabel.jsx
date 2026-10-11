import React from 'react';
import { cn } from '../../utils/cn';
import { MEDIA_CATEGORIES } from '../../utils/constants';

/**
 * MediaCategoryLabel — Visual badge displaying media category (Movie, Series, Manga, Manhwa, Game).
 */
export function MediaCategoryLabel({ category, size = 'sm', className }) {
  if (!category) return null;

  const normalized = String(category).toUpperCase();
  const config = MEDIA_CATEGORIES[normalized] || {
    key: normalized,
    label: normalized,
    badgeClass: 'bg-surface-2 text-text-secondary border-border-neutral',
  };

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[10px] tracking-wider uppercase font-semibold',
    sm: 'px-2 py-0.5 text-xs tracking-wider uppercase font-semibold',
    md: 'px-2.5 py-1 text-xs tracking-wider uppercase font-bold',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded border',
        sizeClasses[size] || sizeClasses.sm,
        config.badgeClass,
        className
      )}
      aria-label={`Category: ${config.label}`}
    >
      {config.label}
    </span>
  );
}
