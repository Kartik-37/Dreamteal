import React from 'react';
import { Link } from 'react-router-dom';
import { Layers, Bookmark, Sparkles, Database, ArrowRight, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { Button } from '../../components/ui/Button';

/**
 * CollectionsPage — Editorial architectural status and overview.
 *
 * Adheres strictly to the DreamTeal project governance:
 * - Does NOT mock or fake persistence with localStorage or local fixtures.
 * - Explains the current state of Collections backend support and specifies the requirements for Phase 6.
 */
export function CollectionsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
      {/* Editorial Header */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal/10 border border-teal/30 text-teal text-xs font-mono uppercase tracking-wider">
          <Layers className="w-3.5 h-3.5" />
          Planned Architecture • Phase 6
        </div>
        <h1 className="text-3xl sm:text-4xl font-serif font-bold text-text-primary tracking-tight">
          Curated Media Collections
        </h1>
        <p className="text-sm sm:text-base text-text-secondary leading-relaxed max-w-2xl">
          Personal and editorial lists for theme-based grouping, franchised marathons, and community curation across Movies, Series, Manga, and Games.
        </p>
      </div>

      {/* Backend Status Notice */}
      <div className="p-6 rounded-2xl bg-surface-1 border border-border-neutral space-y-5">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-electric-gold/10 border border-electric-gold/30 flex items-center justify-center text-electric-gold shrink-0">
            <Database className="w-5 h-5" />
          </div>
          <div className="space-y-1.5">
            <h2 className="text-base font-semibold text-text-primary">
              Backend Integration Status
            </h2>
            <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
              DreamTeal's backend currently provides verified REST endpoints for <strong>Catalog</strong>, <strong>Discovery</strong>, <strong>Tracking & Progress</strong>, <strong>History-Preserving Diary Logs</strong>, <strong>Qualitative Reviews & Reactions</strong>, and <strong>Recommendations</strong>.
              Custom multi-item User Collections have not yet been implemented as a Django REST app.
            </p>
          </div>
        </div>

        {/* Technical Architecture Requirements for Phase 6 */}
        <div className="p-4 rounded-xl bg-surface-2 border border-border-neutral space-y-3 text-xs">
          <div className="font-semibold uppercase tracking-wider text-teal">
            Phase 6 Backend Extension Specification:
          </div>
          <ul className="space-y-2 text-text-secondary">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal shrink-0 mt-0.5" />
              <span><strong>New Django App:</strong> `apps/collections/` with models `MediaCollection` and `CollectionItem`.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal shrink-0 mt-0.5" />
              <span><strong>Entity Relations:</strong> ForeignKeys to `settings.AUTH_USER_MODEL` and `catalog.MediaItem` with sort order index and optional description note per item.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal shrink-0 mt-0.5" />
              <span><strong>Privacy Scoping:</strong> `is_public` boolean flag allowing public editorial lists and private user lists with object-level permissions.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal shrink-0 mt-0.5" />
              <span><strong>REST Endpoints:</strong> `GET/POST /api/v1/collections/` and `GET/PATCH/DELETE /api/v1/collections/&lt;id&gt;/`.</span>
            </li>
          </ul>
        </div>

        <p className="text-xs text-text-muted italic">
          Consistent with our development standards, DreamTeal does not simulate collections using transient browser `localStorage` or fake endpoints.
        </p>
      </div>

      {/* Available Alternatives Callouts */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-5 rounded-xl bg-surface-1 border border-border-neutral space-y-3">
          <div className="flex items-center gap-2 text-teal font-medium text-sm">
            <Bookmark className="w-4 h-4" />
            Active Media Tracker
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            Manage your personal media items using the verified polymorphic tracking system (Watching, Completed, Plan to Watch, Favorites).
          </p>
          <Link
            to="/discovery"
            className="inline-flex items-center gap-1.5 text-xs text-teal font-semibold hover:underline pt-1"
          >
            Explore Catalog <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="p-5 rounded-xl bg-surface-1 border border-border-neutral space-y-3">
          <div className="flex items-center gap-2 text-teal font-medium text-sm">
            <Sparkles className="w-4 h-4" />
            Consumption Diary
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            Preserve your complete chronological history of every film, TV episode, manga chapter, and gaming session.
          </p>
          <Link
            to="/diary"
            className="inline-flex items-center gap-1.5 text-xs text-teal font-semibold hover:underline pt-1"
          >
            Open Diary Timeline <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>
    </div>
  );
}
