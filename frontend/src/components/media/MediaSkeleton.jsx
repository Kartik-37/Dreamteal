import React from 'react';
import { cn } from '../../utils/cn';
import { Skeleton } from '../feedback/Skeleton';

/**
 * MediaSkeleton — Loading placeholder matching MediaPosterCard geometry.
 */
export function MediaSkeleton({ className }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'flex flex-col rounded-xl overflow-hidden bg-surface-1 border border-border-subtle/50',
        className
      )}
    >
      {/* 2:3 Poster skeleton */}
      <Skeleton className="w-full aspect-poster rounded-none" />

      {/* Footer skeleton */}
      <div className="flex flex-col p-3 gap-2 bg-surface-1">
        <Skeleton className="h-4 w-3/4 rounded" />
        <div className="flex items-center justify-between">
          <Skeleton className="h-3 w-1/4 rounded" />
          <Skeleton className="h-3 w-1/3 rounded" />
        </div>
      </div>
    </div>
  );
}
