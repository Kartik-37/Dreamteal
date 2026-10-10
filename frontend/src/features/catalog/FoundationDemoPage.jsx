import React, { useState, useEffect } from 'react';
import { Sparkles, Layers, Sliders, AlertTriangle, RefreshCw, Eye } from 'lucide-react';
import { catalogService } from '../../services/catalog';
import { SAMPLE_MEDIA_ITEMS } from '../../fixtures/mediaFixtures';
import { MediaPosterGrid } from '../../components/media/MediaPosterGrid';
import { MediaCategoryLabel } from '../../components/media/MediaCategoryLabel';
import { ReactionBadge } from '../../components/reactions/ReactionBadge';
import { ReactionSelector } from '../../components/reactions/ReactionSelector';
import { ProgressIndicator } from '../../components/status/ProgressIndicator';
import { MediaMetadata } from '../../components/media/MediaMetadata';
import { MediaBackdrop } from '../../components/media/MediaBackdrop';
import { EmptyState } from '../../components/feedback/EmptyState';
import { ErrorMessage } from '../../components/feedback/ErrorMessage';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { REACTION_LIST, MEDIA_CATEGORIES } from '../../utils/constants';

export function FoundationDemoPage() {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [dataSource, setDataSource] = useState('fixtures'); // 'fixtures' | 'api'
  const [liveItems, setLiveItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Interactive component demo state
  const [interactiveReaction, setInteractiveReaction] = useState('peak');
  const [selectedMedia, setSelectedMedia] = useState(null);
  const [demoStateView, setDemoStateView] = useState('normal'); // 'normal' | 'loading' | 'empty' | 'error'

  // Fetch from backend when switching to API source
  useEffect(() => {
    if (dataSource === 'api') {
      fetchCatalogItems();
    }
  }, [dataSource, selectedCategory]);

  const fetchCatalogItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (selectedCategory !== 'ALL') {
        params.category = selectedCategory;
      }
      const response = await catalogService.getMediaList(params);
      if (response && response.results) {
        setLiveItems(response.results);
      } else if (Array.isArray(response)) {
        setLiveItems(response);
      } else {
        setLiveItems([]);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch catalog items from backend API.');
    } finally {
      setLoading(false);
    }
  };

  // Filter items based on active category
  const currentItems = (dataSource === 'api' ? liveItems : SAMPLE_MEDIA_ITEMS).filter((item) => {
    if (selectedCategory === 'ALL') return true;
    return item.media_type === selectedCategory;
  });

  return (
    <div className="flex flex-col w-full pb-20">
      {/* Editorial Header Section */}
      <section className="relative overflow-hidden border-b border-border-neutral bg-gradient-to-b from-surface-1/60 to-background-deep py-12 sm:py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-teal/10 text-teal border border-teal/20">
              Phase 4 Foundation
            </span>
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-surface-2 text-text-secondary border border-border-neutral">
              Zero Star Ratings
            </span>
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-surface-2 text-text-secondary border border-border-neutral">
              5 Qualitative Reactions
            </span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-text-primary tracking-tight max-w-3xl leading-tight">
            Cinematic media tracking, built for intentional viewing.
          </h1>

          <p className="mt-4 text-base sm:text-lg text-text-secondary max-w-2xl leading-relaxed">
            DreamTeal replaces reductive star ratings with authentic, qualitative verdicts. Track your journey across Movies, Series, Manga, Manhwa, and Video Games.
          </p>

          {/* Interactive Reactions Bar Showcase */}
          <div className="mt-8 p-4 sm:p-5 rounded-xl bg-surface-1/80 border border-border-neutral backdrop-blur-sm max-w-3xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
              <span className="text-xs font-bold text-text-primary uppercase tracking-wider">
                Interactive Reaction System Preview:
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-muted">Active Verdict:</span>
                <ReactionBadge reactionKey={interactiveReaction} size="sm" />
              </div>
            </div>
            <ReactionSelector
              value={interactiveReaction}
              onChange={(key) => setInteractiveReaction(key)}
              size="md"
            />
          </div>
        </div>
      </section>

      {/* Main Grid & Foundation Controls */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 w-full">
        {/* Controls Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border-neutral/60">
          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5" role="tablist" aria-label="Category Filters">
            <button
              type="button"
              role="tab"
              aria-selected={selectedCategory === 'ALL'}
              onClick={() => setSelectedCategory('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors focus-ring ${
                selectedCategory === 'ALL'
                  ? 'bg-teal text-white shadow-sm'
                  : 'bg-surface-1 text-text-secondary hover:text-text-primary hover:bg-surface-2 border border-border-neutral'
              }`}
            >
              All Media
            </button>
            {Object.keys(MEDIA_CATEGORIES).map((catKey) => {
              const cat = MEDIA_CATEGORIES[catKey];
              const isSelected = selectedCategory === catKey;
              return (
                <button
                  key={catKey}
                  type="button"
                  role="tab"
                  aria-selected={isSelected}
                  onClick={() => setSelectedCategory(catKey)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors focus-ring ${
                    isSelected
                      ? 'bg-teal text-white shadow-sm'
                      : 'bg-surface-1 text-text-secondary hover:text-text-primary hover:bg-surface-2 border border-border-neutral'
                  }`}
                >
                  {cat.label}
                </button>
              );
            })}
          </div>

          {/* Data Source & State Demonstrator */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Data Source Toggle */}
            <div className="inline-flex rounded-lg border border-border-neutral p-0.5 bg-surface-1">
              <button
                type="button"
                onClick={() => {
                  setDataSource('fixtures');
                  setDemoStateView('normal');
                }}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  dataSource === 'fixtures'
                    ? 'bg-surface-2 text-teal font-semibold'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                Local Fixtures
              </button>
              <button
                type="button"
                onClick={() => {
                  setDataSource('api');
                  setDemoStateView('normal');
                }}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  dataSource === 'api'
                    ? 'bg-surface-2 text-teal font-semibold'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                Live API
              </button>
            </div>

            {/* State Simulation Toggle */}
            <select
              value={demoStateView}
              onChange={(e) => setDemoStateView(e.target.value)}
              aria-label="Simulate UI state"
              className="px-2.5 py-1 rounded-lg bg-surface-1 border border-border-neutral text-text-secondary text-xs focus-ring"
            >
              <option value="normal">Normal View</option>
              <option value="loading">Loading Skeleton</option>
              <option value="empty">Empty State</option>
              <option value="error">Error State</option>
            </select>
          </div>
        </div>

        {/* State Simulations or Active Grid */}
        <div className="mt-8">
          {demoStateView === 'loading' ? (
            <MediaPosterGrid loading={true} skeletonCount={6} />
          ) : demoStateView === 'empty' ? (
            <EmptyState
              title="No media in this collection"
              description="You have not logged or bookmarked any titles in this category yet."
              action={
                <Button variant="secondary" size="sm" onClick={() => setDemoStateView('normal')}>
                  Reset State
                </Button>
              }
            />
          ) : demoStateView === 'error' ? (
            <ErrorMessage
              title="Catalog Fetch Simulation Error"
              message="Simulated HTTP 500 error: Service temporarily unavailable."
              onRetry={() => setDemoStateView('normal')}
            />
          ) : error ? (
            <ErrorMessage
              title="API Connection Notice"
              message={`${error} (Falling back to local development fixtures)`}
              onRetry={fetchCatalogItems}
            />
          ) : (
            <MediaPosterGrid
              items={currentItems}
              loading={loading}
              onCardClick={(item) => setSelectedMedia(item)}
            />
          )}
        </div>
      </section>

      {/* Media Inspection Modal */}
      {selectedMedia && (
        <Modal
          isOpen={Boolean(selectedMedia)}
          onClose={() => setSelectedMedia(null)}
          title={selectedMedia.title}
          maxWidth="max-w-2xl"
        >
          <div className="flex flex-col gap-4">
            {selectedMedia.backdrop_url && (
              <MediaBackdrop backdropUrl={selectedMedia.backdrop_url} className="min-h-[180px] rounded-lg">
                <div className="flex items-center gap-2">
                  <ReactionBadge reactionKey={selectedMedia.user_reaction || selectedMedia.reaction_consensus} size="sm" />
                  <span className="text-xs text-text-primary font-medium">{selectedMedia.title}</span>
                </div>
              </MediaBackdrop>
            )}

            <MediaMetadata media={selectedMedia} />

            <div className="text-sm text-text-secondary leading-relaxed pt-2 border-t border-border-neutral/60">
              {selectedMedia.synopsis || 'No synopsis available.'}
            </div>

            {selectedMedia.media_type === 'SERIES' && (
              <ProgressIndicator category="SERIES" current={5} total={10} className="mt-2" />
            )}
            {selectedMedia.media_type === 'GAME' && (
              <ProgressIndicator category="GAME" current={34.5} label="34.5 hrs • Main Story" className="mt-2" />
            )}

            <div className="flex justify-end pt-4 border-t border-border-neutral/60">
              <Button variant="secondary" size="sm" onClick={() => setSelectedMedia(null)}>
                Close Preview
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
