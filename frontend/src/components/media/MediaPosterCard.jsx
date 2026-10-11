import React, { useState } from 'react';
import { Film, ImageOff } from 'lucide-react';
import { cn } from '../../utils/cn';
import { ReactionBadge } from '../reactions/ReactionBadge';
import { MediaCategoryLabel } from './MediaCategoryLabel';
import { MediaStatusBadge } from '../status/MediaStatusBadge';

/**
 * MediaPosterCard — Core media presentation card.
 *
 * Supports Movies, TV Series, Manga, Manhwa, and Video Games.
 * Features:
 * - Proper aspect ratio per category (2:3 vertical poster, 16:9 for games)
 * - Graceful image fallback handling (no broken icon, no layout shift)
 * - Text-based qualitative reaction badge (zero star ratings)
 * - Category badge and release year
 * - Optional status indicator
 * - Keyboard accessible focus styles
 */
export function MediaPosterCard({
  media,
  onClick,
  showCategory = true,
  showReaction = true,
  showStatus = true,
  className,
}) {
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  if (!media) return null;

  const {
    title,
    release_year: releaseYear,
    media_type: mediaType,
    poster_url: posterUrl,
    reaction_consensus: reactionConsensus,
    user_reaction: userReaction,
    status,
    slug,
  } = media;

  const displayReaction = userReaction || reactionConsensus;
  const isGame = mediaType === 'GAME';
  const aspectClass = isGame ? 'aspect-game' : 'aspect-poster';

  const handleClick = (e) => {
    if (onClick) {
      e.preventDefault();
      onClick(media);
    }
  };

  return (
    <article
      onClick={handleClick}
      tabIndex={0}
      role="button"
      aria-label={`${title} (${releaseYear || 'Unknown year'}) - ${mediaType}`}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && onClick) {
          e.preventDefault();
          onClick(media);
        }
      }}
      className={cn(
        'group relative flex flex-col rounded-xl overflow-hidden bg-surface-1 border border-border-neutral/70 shadow-card hover:shadow-card-hover hover:border-border-neutral transition-all duration-200 cursor-pointer focus-ring',
        className
      )}
    >
      {/* Poster Media Container */}
      <div className={cn('relative w-full overflow-hidden bg-surface-2', aspectClass)}>
        {posterUrl && !imageError ? (
          <>
            {/* Shimmer placeholder until image loads to prevent layout shift */}
            {!imageLoaded && (
              <div
                className="absolute inset-0 bg-surface-2 animate-pulse flex items-center justify-center text-text-muted"
                aria-hidden="true"
              >
                <Film className="w-8 h-8 opacity-20" />
              </div>
            )}
            <img
              src={posterUrl}
              alt={title}
              loading="lazy"
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
              className={cn(
                'w-full h-full object-cover transition-transform duration-300 group-hover:scale-105',
                imageLoaded ? 'opacity-100' : 'opacity-0'
              )}
            />
          </>
        ) : (
          /* Graceful missing / broken image placeholder */
          <div
            className="w-full h-full flex flex-col items-center justify-center p-4 bg-surface-2 text-text-muted select-none text-center"
            aria-label="No poster available"
          >
            <ImageOff className="w-10 h-10 mb-2 opacity-30" />
            <span className="text-xs font-medium text-text-secondary line-clamp-2 px-2">
              {title}
            </span>
            <span className="text-[10px] text-text-muted mt-1 uppercase tracking-wider">
              No Poster
            </span>
          </div>
        )}

        {/* Top Badges Overlay (Category & Status) */}
        <div className="absolute top-2.5 left-2.5 right-2.5 flex items-start justify-between gap-1.5 pointer-events-none">
          {showCategory && mediaType && (
            <MediaCategoryLabel category={mediaType} size="xs" />
          )}
          {showStatus && status && (
            <MediaStatusBadge status={status} size="xs" />
          )}
        </div>

        {/* Bottom Reaction Verdict Chip */}
        {showReaction && displayReaction && (
          <div className="absolute bottom-2.5 left-2.5 pointer-events-none">
            <ReactionBadge reactionKey={displayReaction} size="xs" />
          </div>
        )}

        {/* Hover Vignette Overlay */}
        <div
          className="absolute inset-0 bg-gradient-to-t from-background-deep/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"
          aria-hidden="true"
        />
      </div>

      {/* Card Metadata Footer */}
      <div className="flex flex-col p-3 gap-1 bg-surface-1 flex-1 justify-between">
        <h3
          className="text-sm font-semibold text-text-primary group-hover:text-teal transition-colors line-clamp-1"
          title={title}
        >
          {title}
        </h3>
        <div className="flex items-center justify-between text-xs text-text-secondary">
          <span>{releaseYear || '—'}</span>
          {media.genres && media.genres.length > 0 && (
            <span className="truncate max-w-[120px] text-text-muted text-[11px]">
              {media.genres[0]}
            </span>
          )}
        </div>
      </div>
    </article>
  );
}
