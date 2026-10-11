import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, SlidersHorizontal, Sparkles, TrendingUp, Clock, Flame, Calendar, RefreshCw, X, ArrowRight, ExternalLink } from 'lucide-react';
import { catalogService } from '../../services/catalog';
import { MediaPosterCard } from '../../components/media/MediaPosterCard';
import { MediaSkeleton } from '../../components/media/MediaSkeleton';
import { Button } from '../../components/ui/Button';
import { ErrorMessage } from '../../components/feedback/ErrorMessage';
import { EmptyState } from '../../components/feedback/EmptyState';


const CATEGORY_TABS = [
  { key: 'ALL', label: 'All Media', categoryParam: null, providerCat: null },
  { key: 'MOVIE', label: 'Movies', categoryParam: 'MOVIE', providerCat: 'movies' },
  { key: 'SERIES', label: 'TV Series', categoryParam: 'SERIES', providerCat: 'series' },
  { key: 'MANGA', label: 'Manga', categoryParam: 'MANGA', providerCat: 'manga' },
  { key: 'MANHWA', label: 'Manhwa', categoryParam: 'MANHWA', providerCat: 'manhwa' },
  { key: 'GAME', label: 'Games', categoryParam: 'GAME', providerCat: 'games' },
];

const DISCOVERY_MODES = [
  { key: 'catalog', label: 'Local Catalog', icon: Sparkles },
  { key: 'popular', label: 'Popular', icon: Flame },
  { key: 'trending', label: 'Trending', icon: TrendingUp },
  { key: 'latest', label: 'New Releases', icon: Clock },
  { key: 'upcoming', label: 'Upcoming', icon: Calendar },
];

export function DiscoveryPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // URL / State synchronization
  const initialCategory = searchParams.get('category') || 'ALL';
  const initialMode = searchParams.get('mode') || 'catalog';
  const initialQuery = searchParams.get('q') || '';

  const [activeCategory, setActiveCategory] = useState(initialCategory);
  const [activeMode, setActiveMode] = useState(initialMode);
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);

  const [ordering, setOrdering] = useState('-release_year');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [importingId, setImportingId] = useState(null);
  const [error, setError] = useState(null);

  // Request race-condition / stale protection
  const activeReqIdRef = useRef(0);

  // Debounce search query input (350ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery.trim());
    }, 350);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Sync state changes to URL
  useEffect(() => {
    const params = new URLSearchParams();
    if (activeCategory !== 'ALL') params.set('category', activeCategory);
    if (activeMode !== 'catalog') params.set('mode', activeMode);
    if (debouncedQuery) params.set('q', debouncedQuery);
    setSearchParams(params, { replace: true });
  }, [activeCategory, activeMode, debouncedQuery, setSearchParams]);

  // Main data fetcher
  const fetchData = useCallback(async (isLoadMore = false) => {
    const reqId = ++activeReqIdRef.current;
    setError(null);
    if (!isLoadMore) {
      setLoading(true);
    }

    try {
      const selectedTab = CATEGORY_TABS.find((t) => t.key === activeCategory) || CATEGORY_TABS[0];

      // 1. If user is actively searching via text
      if (debouncedQuery) {
        const searchCat = selectedTab.key === 'ALL' ? undefined : selectedTab.key.toLowerCase();
        const res = await catalogService.searchMedia({
          q: debouncedQuery,
          category: searchCat,
          limit: 24,
        });

        if (reqId !== activeReqIdRef.current) return; // Stale check
        const rawResults = res?.results || [];
        // Map search results to standard card props
        const mapped = rawResults.map((r) => ({
          id: r.external_id || r.id,
          title: r.title,
          slug: r.local_slug,
          media_type: r.media_type,
          release_year: r.release_year,
          poster_url: r.poster_url,
          is_imported: r.is_imported,
          provider: r.provider,
          external_id: r.external_id,
          synopsis: r.overview,
        }));
        setItems(mapped);
        setHasMore(false);
      }
      // 2. If provider-backed discovery feed (popular, trending, latest, upcoming)
      else if (activeMode !== 'catalog' && selectedTab.providerCat) {
        const res = await catalogService.getDiscovery(selectedTab.providerCat, {
          mode: activeMode,
          limit: 24,
        });

        if (reqId !== activeReqIdRef.current) return; // Stale check
        const rawResults = res?.results || [];
        const mapped = rawResults.map((r) => ({
          id: r.external_id || r.id,
          title: r.title,
          slug: r.local_slug,
          media_type: r.media_type,
          release_year: r.release_year,
          poster_url: r.poster_url,
          is_imported: r.is_imported,
          provider: r.provider,
          external_id: r.external_id,
          synopsis: r.overview,
        }));
        setItems(mapped);
        setHasMore(false);
      }
      // 3. Local catalog browsing
      else {
        const currentPage = isLoadMore ? page + 1 : 1;
        const params = {
          page: currentPage,
          ordering,
        };
        if (selectedTab.categoryParam) {
          params.category = selectedTab.categoryParam;
        }

        const res = await catalogService.getMediaList(params);
        if (reqId !== activeReqIdRef.current) return; // Stale check

        const newItems = res?.results || (Array.isArray(res) ? res : []);
        if (isLoadMore) {
          setItems((prev) => [...prev, ...newItems]);
          setPage(currentPage);
        } else {
          setItems(newItems);
          setPage(1);
        }
        setHasMore(Boolean(res?.next));
      }
    } catch (err) {
      if (reqId === activeReqIdRef.current) {
        console.error('Discovery fetch error:', err);
        setError(err.message || 'Failed to load media catalog.');
      }
    } finally {
      if (reqId === activeReqIdRef.current) {
        setLoading(false);
      }
    }
  }, [activeCategory, activeMode, debouncedQuery, ordering, page]);

  useEffect(() => {
    fetchData(false);
  }, [activeCategory, activeMode, debouncedQuery, ordering]);

  // Click card handler (handles imported vs non-imported items)
  const handleCardClick = async (media) => {
    if (media.slug) {
      navigate(`/media/${media.slug}`);
      return;
    }

    // Need on-demand import
    if (media.provider && media.external_id) {
      setImportingId(media.external_id);
      try {
        const imported = await catalogService.importMedia({
          provider: media.provider,
          external_id: media.external_id,
          media_type: media.media_type,
        });
        if (imported?.slug) {
          navigate(`/media/${imported.slug}`);
        }
      } catch (err) {
        alert(err.message || 'Failed to import media item into catalog.');
      } finally {
        setImportingId(null);
      }
    }
  };

  const currentTab = CATEGORY_TABS.find((t) => t.key === activeCategory) || CATEGORY_TABS[0];
  const canUseDiscoveryFeeds = Boolean(currentTab.providerCat);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Editorial Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl sm:text-4xl font-serif font-bold text-text-primary tracking-tight">
          Discovery Hub
        </h1>
        <p className="text-sm sm:text-base text-text-secondary max-w-2xl leading-relaxed">
          Curated tracking and exploration across Movies, TV Series, Manga, Manhwa, and Video Games.
          Pure editorial perspective with zero star ratings.
        </p>
      </div>

      {/* Primary Category Navigation Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-border-neutral no-scrollbar">
        {CATEGORY_TABS.map((tab) => {
          const isActive = activeCategory === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => {
                setActiveCategory(tab.key);
                // If switching to ALL and mode was external feed, reset to catalog
                if (tab.key === 'ALL' && activeMode !== 'catalog') {
                  setActiveMode('catalog');
                }
              }}
              className={`px-4 py-2 rounded-lg text-xs sm:text-sm font-medium uppercase tracking-wider transition-all whitespace-nowrap focus-ring ${
                isActive
                  ? 'bg-teal text-background-deep font-semibold shadow-sm'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-2'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Control Bar: Search + Discovery Mode / Ordering */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Search input with live debounce */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search ${currentTab.label}...`}
            className="w-full pl-10 pr-9 py-2.5 rounded-xl border border-border-neutral bg-surface-1 text-sm text-text-primary placeholder:text-text-muted focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-0.5 rounded"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Feed Mode or Ordering Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Feed Modes if category supports provider discovery and not searching */}
          {!debouncedQuery && canUseDiscoveryFeeds && (
            <div className="inline-flex rounded-lg border border-border-neutral bg-surface-1 p-0.5 text-xs">
              {DISCOVERY_MODES.map((mode) => {
                const Icon = mode.icon;
                const isSelected = activeMode === mode.key;
                return (
                  <button
                    key={mode.key}
                    onClick={() => setActiveMode(mode.key)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                      isSelected
                        ? 'bg-surface-3 text-teal font-semibold shadow-xs'
                        : 'text-text-secondary hover:text-text-primary hover:bg-surface-2'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">{mode.label}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Ordering dropdown (for local catalog mode) */}
          {!debouncedQuery && activeMode === 'catalog' && (
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-medium text-text-muted flex items-center gap-1">
                <SlidersHorizontal className="w-3 h-3 text-teal" />
                Sort:
              </span>
              <select
                value={ordering}
                onChange={(e) => setOrdering(e.target.value)}
                className="bg-surface-1 border border-border-neutral rounded-lg px-3 py-1.5 text-xs text-text-primary focus:border-teal focus:outline-none"
              >
                <option value="-release_year">Newest First</option>
                <option value="release_year">Oldest First</option>
                <option value="title">Title (A-Z)</option>
                <option value="-created_at">Recently Added</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Active Search / Feed indicator */}
      {debouncedQuery && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-surface-1 border border-border-neutral text-xs text-text-secondary">
          <span>
            Showing search results for <strong className="text-teal">"{debouncedQuery}"</strong> in {currentTab.label}
          </span>
          <button
            onClick={() => setSearchQuery('')}
            className="text-text-muted hover:text-text-primary underline text-[11px]"
          >
            Clear Search
          </button>
        </div>
      )}

      {/* Error state */}
      {error && (
        <ErrorMessage
          message={error}
          actionLabel="Try Again"
          onAction={() => fetchData(false)}
        />
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6">
          {Array.from({ length: 12 }).map((_, idx) => (
            <MediaSkeleton key={idx} />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && items.length === 0 && (
        <EmptyState
          title={debouncedQuery ? 'No matching media found' : 'Catalog empty'}
          message={
            debouncedQuery
              ? `We couldn't find any results matching "${debouncedQuery}". Try refining your query or browsing discovery feeds.`
              : 'No items currently in this view. Try another category or discovery mode.'
          }
          actionLabel={debouncedQuery ? 'Clear Search' : 'Browse Popular'}
          onAction={() => {
            if (debouncedQuery) {
              setSearchQuery('');
            } else {
              setActiveMode('popular');
            }
          }}
        />
      )}

      {/* Results Poster Grid */}
      {!loading && items.length > 0 && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6">
            {items.map((media) => (
              <div key={media.id || media.slug} className="relative">
                <MediaPosterCard
                  media={media}
                  onClick={() => handleCardClick(media)}
                />
                {/* On-demand importing badge overlay */}
                {importingId === media.external_id && (
                  <div className="absolute inset-0 bg-background-deep/80 backdrop-blur-xs rounded-xl flex flex-col items-center justify-center p-3 text-center space-y-2 z-10">
                    <RefreshCw className="w-5 h-5 text-teal animate-spin" />
                    <span className="text-[11px] text-teal font-medium">Adding to Catalog...</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Load More Button for local catalog */}
          {!debouncedQuery && activeMode === 'catalog' && hasMore && (
            <div className="pt-6 flex justify-center">
              <Button
                variant="outline"
                onClick={() => fetchData(true)}
                className="px-6 py-2.5 text-xs font-semibold uppercase tracking-wider"
              >
                Load More Items
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
