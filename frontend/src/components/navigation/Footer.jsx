import React from 'react';
import { REACTIONS } from '../../utils/constants';

export function Footer() {
  return (
    <footer className="w-full border-t border-border-neutral bg-surface-1/50 py-12 px-4 sm:px-6 lg:px-8 mt-auto">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
        {/* Left: Brand Identity & Philosophy */}
        <div className="flex flex-col gap-2 max-w-sm">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-teal shadow-glow inline-block" />
            <span className="text-base font-bold text-text-primary tracking-tight">
              Dream<span className="text-teal">Teal</span>
            </span>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            A cinematic, qualitative entertainment tracking experience. Zero star ratings, zero numeric averages — strictly authentic reactions across Movies, Series, Manga, Manhwa, and Video Games.
          </p>
        </div>

        {/* Center: Reactions Palette Summary */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-semibold text-text-primary uppercase tracking-wider">
            Universal Reactions
          </span>
          <div className="flex flex-wrap gap-1.5">
            {Object.values(REACTIONS).map((r) => (
              <span
                key={r.key}
                className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${r.badgeClass}`}
              >
                {r.label}
              </span>
            ))}
          </div>
        </div>

        {/* Right: Attribution & Notice */}
        <div className="flex flex-col gap-1 text-xs text-text-muted md:text-right">
          <span>Metadata powered by TMDB, AniList, Jikan & RAWG.</span>
          <span>© {new Date().getFullYear()} DreamTeal. All rights reserved.</span>
        </div>
      </div>
    </footer>
  );
}
