import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Bookmark, Heart, Check, Clock, Tv, BookOpen, Gamepad2, Film,
  Calendar, Building, User, Layers, Share2, AlertCircle, ArrowLeft,
  Plus, Edit3, MessageSquare, Eye, EyeOff, Sparkles, ExternalLink
} from 'lucide-react';
import { catalogService } from '../../services/catalog';
import { trackingService } from '../../services/tracking';
import { reviewService } from '../../services/reviews';
import { recommendationService } from '../../services/recommendations';
import { useAuth } from '../auth/AuthContext';
import { MediaBackdrop } from '../../components/media/MediaBackdrop';
import { MediaCategoryLabel } from '../../components/media/MediaCategoryLabel';
import { ReactionBadge } from '../../components/reactions/ReactionBadge';
import { MediaPosterCard } from '../../components/media/MediaPosterCard';
import { SafeMarkdown } from '../../components/ui/SafeMarkdown';
import { Button } from '../../components/ui/Button';
import { LoadingSpinner } from '../../components/feedback/LoadingSpinner';
import { ErrorMessage } from '../../components/feedback/ErrorMessage';
import { EmptyState } from '../../components/feedback/EmptyState';
import { TrackingModal } from '../tracking/TrackingModal';
import { ReviewModal } from '../reviews/ReviewModal';
import { DiaryModal } from '../diary/DiaryModal';

export function MediaDetailPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();

  // Media data states
  const [media, setMedia] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Tracking states
  const [userStatus, setUserStatus] = useState(null);
  const [userProgress, setUserProgress] = useState(null);
  const [isTrackingModalOpen, setIsTrackingModalOpen] = useState(false);

  // Review states
  const [reviews, setReviews] = useState([]);
  const [userReview, setUserReview] = useState(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [revealedSpoilers, setRevealedSpoilers] = useState(new Set());

  // Diary modal state
  const [isDiaryModalOpen, setIsDiaryModalOpen] = useState(false);

  // Recommendations state
  const [recommendations, setRecommendations] = useState([]);
  const [recLoading, setRecLoading] = useState(false);

  // Load media details
  const fetchMedia = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const data = await catalogService.getMediaDetail(slug);
      setMedia(data);
    } catch (err) {
      console.error('Failed to load media detail:', err);
      setError(err.status === 404 ? 'Media item not found.' : (err.message || 'Failed to load media item.'));
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchMedia();
  }, [fetchMedia]);

  // Load user tracking & review data once media is fetched
  const fetchUserEngagements = useCallback(async () => {
    if (!media?.id) return;

    // 1. Fetch public reviews
    try {
      const revRes = await reviewService.getMediaReviews(media.id);
      const revList = revRes?.results || (Array.isArray(revRes) ? revRes : []);
      setReviews(revList);

      if (isAuthenticated && user) {
        const found = revList.find((r) => r.user === user.id || r.username === user.username);
        setUserReview(found || null);
      }
    } catch (err) {
      console.warn('Reviews fetch failed:', err);
    }

    // 2. If authenticated, fetch status and progress
    if (isAuthenticated) {
      try {
        const statusObj = await trackingService.getStatusForMedia(media.id);
        setUserStatus(statusObj);
      } catch (err) {
        console.warn('Status fetch failed:', err);
      }

      try {
        const progObj = await trackingService.getProgressForMedia(media.id);
        setUserProgress(progObj);
      } catch (err) {
        console.warn('Progress fetch failed:', err);
      }
    }
  }, [media, isAuthenticated, user]);

  useEffect(() => {
    fetchUserEngagements();
  }, [fetchUserEngagements]);

  // Load recommendations
  useEffect(() => {
    if (!slug) return;
    setRecLoading(true);
    recommendationService.getNext(slug, { cross_category: true, limit: 6 })
      .then((res) => {
        setRecommendations(res?.recommendations || []);
      })
      .catch((err) => {
        console.warn('Recommendations fetch non-critical failure:', err);
        setRecommendations([]);
      })
      .finally(() => {
        setRecLoading(false);
      });
  }, [slug]);

  const toggleSpoiler = (reviewId) => {
    setRevealedSpoilers((prev) => {
      const next = new Set(prev);
      if (next.has(reviewId)) next.delete(reviewId);
      else next.add(reviewId);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <LoadingSpinner size="lg" />
        <p className="text-xs text-text-muted">Loading media experience...</p>
      </div>
    );
  }

  if (error || !media) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20">
        <EmptyState
          title={error === 'Media item not found.' ? 'Item Not Found' : 'Error Loading Media'}
          message={error || 'This media item could not be retrieved from the catalog.'}
          actionLabel="Back to Discovery"
          onAction={() => navigate('/discovery')}
        />
      </div>
    );
  }

  const {
    title,
    release_year: releaseYear,
    media_type: mediaType,
    poster_url: posterUrl,
    backdrop_url: backdropUrl,
    synopsis,
    genres = [],
    tags = [],
    movie_detail: movieDetail,
    series_detail: seriesDetail,
    manga_detail: mangaDetail,
    game_detail: gameDetail,
    external_mappings: externalMappings = [],
  } = media;

  const isGame = mediaType === 'GAME';

  return (
    <div className="min-h-screen pb-20">
      {/* Editorial Hero Backdrop */}
      <div className="relative">
        <MediaBackdrop
          backdropUrl={backdropUrl}
          title={title}
          height="lg"
          gradient="strong"
        />

        {/* Back navigation */}
        <div className="absolute top-6 left-4 sm:left-8 z-20">
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-1/80 backdrop-blur-md border border-border-neutral/80 text-xs text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 -mt-32 sm:-mt-44 relative z-10 space-y-12">
        {/* Header Grid: Poster + Metadata */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          {/* Poster Column */}
          <div className="md:col-span-4 lg:col-span-3 flex flex-col items-center sm:items-start space-y-4">
            <div
              className={`w-48 sm:w-60 md:w-full rounded-2xl overflow-hidden border-2 border-border-neutral/80 shadow-2xl bg-surface-2 ${
                isGame ? 'aspect-game' : 'aspect-poster'
              }`}
            >
              {posterUrl ? (
                <img
                  src={posterUrl}
                  alt={title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center p-4 text-text-muted">
                  <Film className="w-10 h-10 opacity-30 mb-2" />
                  <span className="text-xs">No Poster Available</span>
                </div>
              )}
            </div>

            {/* Quick Action CTAs */}
            <div className="w-full space-y-2 pt-2">
              <Button
                variant={userStatus ? 'outline' : 'primary'}
                className="w-full justify-center text-xs font-semibold uppercase tracking-wider"
                onClick={() => {
                  if (!isAuthenticated) {
                    navigate('/login');
                  } else {
                    setIsTrackingModalOpen(true);
                  }
                }}
              >
                <Bookmark className="w-4 h-4 mr-1.5" />
                {userStatus ? `Status: ${userStatus.status_display || userStatus.status}` : 'Track Progress'}
              </Button>

              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  className="w-full justify-center text-xs"
                  onClick={() => {
                    if (!isAuthenticated) navigate('/login');
                    else setIsReviewModalOpen(true);
                  }}
                >
                  <MessageSquare className="w-3.5 h-3.5 mr-1" />
                  {userReview ? 'Edit Review' : 'Review'}
                </Button>

                <Button
                  variant="outline"
                  className="w-full justify-center text-xs"
                  onClick={() => {
                    if (!isAuthenticated) navigate('/login');
                    else setIsDiaryModalOpen(true);
                  }}
                >
                  <Calendar className="w-3.5 h-3.5 mr-1" />
                  Log Diary
                </Button>
              </div>
            </div>
          </div>

          {/* Details Column */}
          <div className="md:col-span-8 lg:col-span-9 space-y-6 pt-4 md:pt-16">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2.5">
                <MediaCategoryLabel category={mediaType} />
                {releaseYear && (
                  <span className="px-2 py-0.5 rounded text-xs font-mono text-text-muted bg-surface-2 border border-border-neutral">
                    {releaseYear}
                  </span>
                )}
                {userStatus?.is_favorite && (
                  <span className="inline-flex items-center gap-1 text-xs text-warm-coral px-2 py-0.5 rounded bg-warm-coral/10 border border-warm-coral/30">
                    <Heart className="w-3 h-3 fill-warm-coral" />
                    Favorited
                  </span>
                )}
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-bold text-text-primary tracking-tight">
                {title}
              </h1>
            </div>

            {/* Genres & Tags */}
            <div className="flex flex-wrap items-center gap-2">
              {genres.map((g) => (
                <span
                  key={g.id || g.slug}
                  className="px-2.5 py-1 rounded-md text-xs font-medium bg-surface-2 text-text-secondary border border-border-neutral"
                >
                  {g.name}
                </span>
              ))}
              {tags.map((t) => (
                <span
                  key={t.id || t.slug}
                  className="px-2.5 py-1 rounded-md text-xs font-mono text-text-muted bg-surface-1 border border-border-neutral/60"
                >
                  #{t.name}
                </span>
              ))}
            </div>

            {/* Synopsis */}
            {synopsis && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Synopsis
                </h3>
                <p className="text-sm sm:text-base leading-relaxed text-text-secondary max-w-3xl">
                  {synopsis}
                </p>
              </div>
            )}

            {/* Category-Specific Extensions Info */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-surface-1 border border-border-neutral text-xs">
              {movieDetail && (
                <>
                  {movieDetail.director && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Director</div>
                      <div className="font-medium text-text-primary mt-0.5">{movieDetail.director}</div>
                    </div>
                  )}
                  {movieDetail.runtime_minutes && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Runtime</div>
                      <div className="font-medium text-text-primary mt-0.5">{movieDetail.runtime_minutes} mins</div>
                    </div>
                  )}
                  {movieDetail.studio && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Studio</div>
                      <div className="font-medium text-text-primary mt-0.5">{movieDetail.studio}</div>
                    </div>
                  )}
                </>
              )}

              {seriesDetail && (
                <>
                  {seriesDetail.creators && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Creators</div>
                      <div className="font-medium text-text-primary mt-0.5">{seriesDetail.creators}</div>
                    </div>
                  )}
                  {seriesDetail.total_seasons !== undefined && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Seasons</div>
                      <div className="font-medium text-text-primary mt-0.5">{seriesDetail.total_seasons}</div>
                    </div>
                  )}
                  {seriesDetail.total_episodes !== undefined && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Episodes</div>
                      <div className="font-medium text-text-primary mt-0.5">{seriesDetail.total_episodes}</div>
                    </div>
                  )}
                </>
              )}

              {mangaDetail && (
                <>
                  {mangaDetail.author && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Author</div>
                      <div className="font-medium text-text-primary mt-0.5">{mangaDetail.author}</div>
                    </div>
                  )}
                  {mangaDetail.status && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Status</div>
                      <div className="font-medium text-text-primary mt-0.5">{mangaDetail.status}</div>
                    </div>
                  )}
                  {mangaDetail.total_chapters !== undefined && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Chapters</div>
                      <div className="font-medium text-text-primary mt-0.5">{mangaDetail.total_chapters || 'Ongoing'}</div>
                    </div>
                  )}
                </>
              )}

              {gameDetail && (
                <>
                  {gameDetail.developer && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Developer</div>
                      <div className="font-medium text-text-primary mt-0.5">{gameDetail.developer}</div>
                    </div>
                  )}
                  {gameDetail.platforms && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Platforms</div>
                      <div className="font-medium text-text-primary mt-0.5">{gameDetail.platforms}</div>
                    </div>
                  )}
                  {gameDetail.average_story_hours && (
                    <div>
                      <div className="text-text-muted uppercase text-[10px] tracking-wider">Main Story</div>
                      <div className="font-medium text-text-primary mt-0.5">{gameDetail.average_story_hours} hours</div>
                    </div>
                  )}
                </>
              )}

              {/* External Provider Identity mapping links */}
              {externalMappings.length > 0 && (
                <div className="col-span-full pt-2 border-t border-border-neutral/60 flex flex-wrap items-center gap-3">
                  <span className="text-[10px] uppercase font-semibold text-text-muted">Verified Providers:</span>
                  {externalMappings.map((m) => (
                    <a
                      key={m.id || m.provider_key}
                      href={m.external_url || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] text-teal hover:underline"
                    >
                      <span>{m.provider_name || m.provider_key}</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* User Active Progress Snapshot (if tracked) */}
        {userProgress && (
          <div className="p-4 rounded-xl bg-surface-1 border border-teal/30 space-y-2">
            <div className="text-xs font-semibold uppercase tracking-wider text-teal flex items-center gap-2">
              <Check className="w-4 h-4 text-teal" />
              Your Active Progress
            </div>
            <div className="text-sm text-text-primary font-medium">
              {userProgress.series_progress && (
                <span>Currently on Season {userProgress.series_progress.current_season}, Episode {userProgress.series_progress.current_episode}</span>
              )}
              {userProgress.manga_progress && (
                <span>Currently on Chapter {userProgress.manga_progress.current_chapter} {userProgress.manga_progress.current_volume ? `(Volume ${userProgress.manga_progress.current_volume})` : ''}</span>
              )}
              {userProgress.game_progress && (
                <span>Invested {userProgress.game_progress.hours_played} hours {userProgress.game_progress.platform_played_on ? `on ${userProgress.game_progress.platform_played_on}` : ''}</span>
              )}
            </div>
          </div>
        )}

        {/* "What to consume next" Recommendation Section */}
        <div className="space-y-6 pt-4 border-t border-border-neutral">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl sm:text-2xl font-serif font-bold text-text-primary flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-teal" />
                What to Consume Next
              </h2>
              <p className="text-xs sm:text-sm text-text-secondary mt-0.5">
                Explainable, deterministic cross-category recommendations based on thematic and structural resonance.
              </p>
            </div>
          </div>

          {recLoading && (
            <div className="py-12 flex justify-center">
              <LoadingSpinner size="md" />
            </div>
          )}

          {!recLoading && recommendations.length === 0 && (
            <p className="text-xs text-text-muted italic py-4">
              No matching recommendations currently available for this title in the catalog.
            </p>
          )}

          {!recLoading && recommendations.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {recommendations.map((rec) => {
                const recItem = rec.media_item;
                const reason = rec.primary_reason?.detail || rec.primary_reason?.label;
                return (
                  <div key={recItem.id || recItem.slug} className="space-y-1.5">
                    <MediaPosterCard
                      media={recItem}
                      onClick={() => navigate(`/media/${recItem.slug}`)}
                    />
                    {reason && (
                      <p className="text-[11px] text-teal/90 line-clamp-2 px-1">
                        {reason}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Qualitative Reviews and Community Reactions Section */}
        <div className="space-y-6 pt-6 border-t border-border-neutral">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl sm:text-2xl font-serif font-bold text-text-primary">
                Qualitative Reactions & Reviews
              </h2>
              <p className="text-xs sm:text-sm text-text-secondary mt-0.5">
                Editorial reactions and written critique. Zero stars, non-numeric verdict badges only.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (!isAuthenticated) navigate('/login');
                else setIsReviewModalOpen(true);
              }}
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              {userReview ? 'Edit Review' : 'Add Review'}
            </Button>
          </div>

          {reviews.length === 0 ? (
            <EmptyState
              title="No reviews yet"
              message="Be the first to share your qualitative reaction and critique on this title."
              actionLabel="Write Review"
              onAction={() => {
                if (!isAuthenticated) navigate('/login');
                else setIsReviewModalOpen(true);
              }}
            />
          ) : (
            <div className="space-y-4">
              {reviews.map((rev) => {
                const reactionKey = rev.reaction_key || rev.reaction_detail?.key;
                const isOwner = user && (rev.user === user.id || rev.username === user.username);
                const hasSpoilers = Boolean(rev.contains_spoilers);
                const isRevealed = revealedSpoilers.has(rev.id);

                return (
                  <div
                    key={rev.id}
                    className="p-5 rounded-xl bg-surface-1 border border-border-neutral space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-sm text-text-primary">
                          {rev.username || 'Community Member'}
                        </span>
                        {reactionKey && (
                          <ReactionBadge reactionKey={reactionKey} size="sm" />
                        )}
                        {!rev.is_public && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-mono bg-surface-2 text-text-muted border border-border-neutral">
                            Private
                          </span>
                        )}
                      </div>

                      {isOwner && (
                        <button
                          onClick={() => setIsReviewModalOpen(true)}
                          className="text-xs text-teal hover:underline flex items-center gap-1"
                        >
                          <Edit3 className="w-3 h-3" />
                          Edit
                        </button>
                      )}
                    </div>

                    {/* Spoiler Mask / Safe Markdown Commentary */}
                    {hasSpoilers && !isRevealed ? (
                      <div className="p-4 rounded-lg bg-surface-2 border border-border-neutral flex items-center justify-between">
                        <span className="text-xs text-crimson font-medium flex items-center gap-1.5">
                          <EyeOff className="w-3.5 h-3.5" />
                          Review contains spoilers
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleSpoiler(rev.id)}
                          className="text-xs text-text-secondary hover:text-text-primary"
                        >
                          Reveal
                        </Button>
                      </div>
                    ) : (
                      rev.review_text && (
                        <SafeMarkdown
                          content={rev.review_text}
                          className="text-xs sm:text-sm text-text-secondary"
                        />
                      )
                    )}

                    <div className="text-[11px] text-text-muted font-mono pt-1">
                      {rev.created_at ? new Date(rev.created_at).toLocaleDateString() : ''}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Tracking Modal */}
      <TrackingModal
        isOpen={isTrackingModalOpen}
        onClose={() => setIsTrackingModalOpen(false)}
        media={media}
        initialStatus={userStatus}
        initialProgress={userProgress}
        onSuccess={() => fetchUserEngagements()}
      />

      {/* Review Modal */}
      <ReviewModal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        media={media}
        initialReview={userReview}
        onSuccess={() => fetchUserEngagements()}
      />

      {/* Diary Modal */}
      <DiaryModal
        isOpen={isDiaryModalOpen}
        onClose={() => setIsDiaryModalOpen(false)}
        media={media}
        onSuccess={() => {}}
      />
    </div>
  );
}
