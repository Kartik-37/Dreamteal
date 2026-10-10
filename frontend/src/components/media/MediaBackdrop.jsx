import React, { useState } from 'react';
import { cn } from '../../utils/cn';

/**
 * MediaBackdrop — Cinematic backdrop hero banner for media presentation.
 * Features dark gradient overlay ensuring high text readability.
 */
export function MediaBackdrop({
  backdropUrl,
  alt = 'Media backdrop',
  children,
  className,
}) {
  const [hasError, setHasError] = useState(false);

  return (
    <div
      className={cn(
        'relative w-full min-h-[280px] sm:min-h-[360px] md:min-h-[440px] overflow-hidden bg-background-elevated',
        className
      )}
    >
      {/* Background Image */}
      {backdropUrl && !hasError && (
        <img
          src={backdropUrl}
          alt={alt}
          onError={() => setHasError(true)}
          className="absolute inset-0 w-full h-full object-cover object-center filter brightness-[0.45] scale-105 transform motion-safe:transition-transform motion-safe:duration-700"
        />
      )}

      {/* Dark Vignette and Gradient Layers for High Contrast Readability */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-background-deep via-background-deep/60 to-transparent"
        aria-hidden="true"
      />
      <div
        className="absolute inset-0 bg-gradient-to-r from-background-deep via-background-deep/40 to-transparent"
        aria-hidden="true"
      />

      {/* Content Container */}
      <div className="relative z-10 w-full h-full flex flex-col justify-end p-6 sm:p-8 md:p-12 max-w-7xl mx-auto">
        {children}
      </div>
    </div>
  );
}
