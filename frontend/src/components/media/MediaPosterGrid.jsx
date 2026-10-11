import React from 'react';
import { cn } from '../../utils/cn';
import { MediaPosterCard } from './MediaPosterCard';
import { MediaSkeleton } from './MediaSkeleton';
import { EmptyState } from '../feedback/EmptyState';

/**
 * MediaPosterGrid — Responsive grid container for media poster cards.
 *
 * Handles:
 * - 2 columns on mobile, 3-4 on tablet, 5-6 on desktop
 * - Skeleton loading state
 * - Empty state fallback
 */
export function MediaPosterGrid({
  items = [],
  loading = false,
  skeletonCount = 6,
  onCardClick,
  emptyTitle = 'No media items found',
  emptyDescription = 'There are no titles matching this view.',
  className,
}) {
  if (loading) {
    return (
      <div
        className={cn(
          'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-5',
          className
        )}
      >
        {Array.from({ length: skeletonCount }).map((_, index) => (
          <MediaSkeleton key={`skeleton-${index}`} />
        ))}
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        className="my-8"
      />
    );
  }

  return (
    <div
      className={cn(
        'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-5',
        className
      )}
    >
      {items.map((item) => (
        <MediaPosterCard
          key={item.id || item.slug}
          media={item}
          onClick={onCardClick}
        />
      ))}
    </div>
  );
}
