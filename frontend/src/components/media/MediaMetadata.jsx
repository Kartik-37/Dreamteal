import React from 'react';
import { cn } from '../../utils/cn';
import { MediaCategoryLabel } from './MediaCategoryLabel';

/**
 * MediaMetadata — Editorial metadata row or panel for media items.
 * Strictly non-numeric ratings; displays clean tags, genres, years, and categories.
 */
export function MediaMetadata({
  media,
  showGenres = true,
  showTags = true,
  className,
}) {
  if (!media) return null;

  const {
    release_year: releaseYear,
    media_type: mediaType,
    genres = [],
    tags = [],
    original_title: originalTitle,
  } = media;

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      {/* Top Meta Attributes Row */}
      <div className="flex flex-wrap items-center gap-2.5 text-xs text-text-secondary">
        {mediaType && <MediaCategoryLabel category={mediaType} size="xs" />}
        {releaseYear && (
          <span className="font-medium text-text-primary">{releaseYear}</span>
        )}
        {originalTitle && originalTitle !== media.title && (
          <>
            <span className="text-border-neutral">•</span>
            <span className="italic text-text-muted">{originalTitle}</span>
          </>
        )}
      </div>

      {/* Genres Row */}
      {showGenres && genres && genres.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {genres.map((genre) => (
            <span
              key={genre}
              className="px-2 py-0.5 rounded text-xs bg-surface-2 text-text-secondary border border-border-neutral/60"
            >
              {genre}
            </span>
          ))}
        </div>
      )}

      {/* Tags Row */}
      {showTags && tags && tags.length > 0 && (
        <div className="flex flex-wrap items-center gap-1 text-[11px] text-text-muted">
          <span className="mr-1">Themes:</span>
          {tags.map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0.5 rounded bg-surface-1 text-text-muted border border-border-subtle"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
