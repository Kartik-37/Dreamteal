import React, { useState, useEffect } from 'react';
import { Bookmark, Check, Trash2, Clock, Tv, BookOpen, Gamepad2, Heart } from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { ErrorMessage } from '../../components/feedback/ErrorMessage';
import { trackingService } from '../../services/tracking';
import { TRACKING_STATUSES } from '../../utils/constants';

export function TrackingModal({
  isOpen,
  onClose,
  media,
  initialStatus = null,
  initialProgress = null,
  onSuccess,
}) {
  const [statusVal, setStatusVal] = useState('WATCHING');
  const [isFavorite, setIsFavorite] = useState(false);

  // Category progress states
  // Series
  const [season, setSeason] = useState(0);
  const [episode, setEpisode] = useState(0);
  const [lastEpisodeTitle, setLastEpisodeTitle] = useState('');

  // Manga
  const [chapter, setChapter] = useState(0);
  const [volume, setVolume] = useState('');

  // Game
  const [hoursPlayed, setHoursPlayed] = useState('0.0');
  const [completionType, setCompletionType] = useState('');
  const [platform, setPlatform] = useState('');

  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  // Synchronize state when opened with initial data
  useEffect(() => {
    if (isOpen) {
      setError(null);
      if (initialStatus) {
        setStatusVal(initialStatus.status || 'WATCHING');
        setIsFavorite(Boolean(initialStatus.is_favorite));
      } else {
        setStatusVal('WATCHING');
        setIsFavorite(false);
      }

      if (initialProgress) {
        if (initialProgress.series_progress) {
          setSeason(initialProgress.series_progress.current_season || 0);
          setEpisode(initialProgress.series_progress.current_episode || 0);
          setLastEpisodeTitle(initialProgress.series_progress.last_watched_episode_title || '');
        }
        if (initialProgress.manga_progress) {
          setChapter(initialProgress.manga_progress.current_chapter || 0);
          setVolume(initialProgress.manga_progress.current_volume ?? '');
        }
        if (initialProgress.game_progress) {
          setHoursPlayed(String(initialProgress.game_progress.hours_played ?? '0.0'));
          setCompletionType(initialProgress.game_progress.completion_type || '');
          setPlatform(initialProgress.game_progress.platform_played_on || '');
        }
      } else {
        setSeason(0);
        setEpisode(0);
        setLastEpisodeTitle('');
        setChapter(0);
        setVolume('');
        setHoursPlayed('0.0');
        setCompletionType('');
        setPlatform('');
      }
    }
  }, [isOpen, initialStatus, initialProgress]);

  if (!media) return null;

  const mediaType = media.media_type;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // 1. Status Mutation (Create or Update)
      let savedStatus = null;
      const statusPayload = {
        media_id: media.id,
        status: statusVal,
        is_favorite: isFavorite,
      };

      if (initialStatus?.id) {
        savedStatus = await trackingService.updateStatus(initialStatus.id, {
          status: statusVal,
          is_favorite: isFavorite,
        });
      } else {
        savedStatus = await trackingService.createStatus(statusPayload);
      }

      // 2. Progress Mutation (if media category supports progress tracking)
      let savedProgress = null;
      if (mediaType === 'SERIES' || mediaType === 'MANGA' || mediaType === 'MANHWA' || mediaType === 'GAME') {
        const progressPayload = {
          media_id: media.id,
        };

        if (mediaType === 'SERIES') {
          progressPayload.series_progress = {
            current_season: Math.max(0, parseInt(season, 10) || 0),
            current_episode: Math.max(0, parseInt(episode, 10) || 0),
            last_watched_episode_title: lastEpisodeTitle || '',
          };
        } else if (mediaType === 'MANGA' || mediaType === 'MANHWA') {
          progressPayload.manga_progress = {
            current_chapter: Math.max(0, parseInt(chapter, 10) || 0),
            current_volume: volume === '' ? null : Math.max(0, parseInt(volume, 10) || 0),
          };
        } else if (mediaType === 'GAME') {
          const parsedHours = parseFloat(hoursPlayed) || 0;
          progressPayload.game_progress = {
            hours_played: Math.max(0, parsedHours).toFixed(1),
            completion_type: completionType || null,
            platform_played_on: platform || null,
          };
        }

        if (initialProgress?.id) {
          savedProgress = await trackingService.updateProgress(initialProgress.id, progressPayload);
        } else {
          try {
            savedProgress = await trackingService.createProgress(progressPayload);
          } catch (progErr) {
            // If already exists via conflict, attempt update
            if (progErr.isConflict && initialProgress?.id) {
              savedProgress = await trackingService.updateProgress(initialProgress.id, progressPayload);
            } else {
              throw progErr;
            }
          }
        }
      }

      if (onSuccess) {
        onSuccess({ status: savedStatus, progress: savedProgress });
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to update tracking details.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!initialStatus?.id) return;
    if (!window.confirm(`Are you sure you want to remove ${media.title} from your tracking list?`)) return;

    setDeleting(true);
    setError(null);
    try {
      await trackingService.deleteStatus(initialStatus.id);
      if (onSuccess) {
        onSuccess({ status: null, progress: initialProgress });
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to remove status.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Track & Progress: ${media.title}`} maxWidth="max-w-lg">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        {error && <ErrorMessage title="Tracking Error" message={error} />}

        {/* Media Snippet Header */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-2/60 border border-border-neutral">
          {media.poster_url ? (
            <img
              src={media.poster_url}
              alt={media.title}
              className="w-12 h-16 object-cover rounded border border-border-neutral/60 shrink-0"
            />
          ) : (
            <div className="w-12 h-16 rounded bg-surface-3 flex items-center justify-center text-text-muted shrink-0 text-xs">
              No Poster
            </div>
          )}
          <div className="flex flex-col min-w-0">
            <h3 className="text-sm font-semibold text-text-primary truncate">{media.title}</h3>
            <span className="text-xs text-text-secondary">
              {media.release_year || '—'} • {media.media_type}
            </span>
          </div>
        </div>

        {/* Status Selector */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
            Consumption Status
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {Object.keys(TRACKING_STATUSES).map((statusKey) => {
              const conf = TRACKING_STATUSES[statusKey];
              const isSelected = statusVal === statusKey;
              return (
                <button
                  key={statusKey}
                  type="button"
                  onClick={() => setStatusVal(statusKey)}
                  className={`flex items-center justify-center p-2 rounded-lg text-xs font-medium border transition-colors focus-ring ${
                    isSelected
                      ? 'bg-teal/15 text-teal border-teal/40 font-semibold'
                      : 'bg-surface-2 text-text-secondary border-border-neutral hover:text-text-primary hover:bg-surface-3'
                  }`}
                >
                  <span>{conf.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Favorite Toggle */}
        <label className="flex items-center gap-2.5 p-3 rounded-lg bg-surface-2/40 border border-border-neutral/60 cursor-pointer hover:bg-surface-2/80 transition-colors">
          <input
            type="checkbox"
            checked={isFavorite}
            onChange={(e) => setIsFavorite(e.target.checked)}
            className="w-4 h-4 rounded text-teal bg-surface-2 border-border-neutral focus-ring"
          />
          <Heart className={`w-4 h-4 ${isFavorite ? 'text-red-400 fill-red-400' : 'text-text-muted'}`} />
          <span className="text-sm text-text-primary font-medium">Add to Favorites</span>
        </label>

        {/* Category Specific Progress Sections */}
        {mediaType === 'SERIES' && (
          <div className="flex flex-col gap-3 p-3.5 rounded-lg bg-surface-2/40 border border-border-neutral">
            <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
              <Tv className="w-4 h-4 text-cyan-400" />
              <span>TV Series Episode Progress</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-text-secondary">Current Season</label>
                <input
                  type="number"
                  min="0"
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary text-sm focus-ring"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-text-secondary">Current Episode</label>
                <input
                  type="number"
                  min="0"
                  value={episode}
                  onChange={(e) => setEpisode(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary text-sm focus-ring"
                />
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-text-secondary">Last Episode Title (Optional)</label>
              <input
                type="text"
                placeholder="e.g. The Grim Reaping"
                value={lastEpisodeTitle}
                onChange={(e) => setLastEpisodeTitle(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary text-sm focus-ring placeholder:text-text-muted"
              />
            </div>
          </div>
        )}

        {(mediaType === 'MANGA' || mediaType === 'MANHWA') && (
          <div className="flex flex-col gap-3 p-3.5 rounded-lg bg-surface-2/40 border border-border-neutral">
            <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              <span>Manga / Manhwa Reading Progress</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-text-secondary">Current Chapter</label>
                <input
                  type="number"
                  min="0"
                  value={chapter}
                  onChange={(e) => setChapter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary text-sm focus-ring"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-text-secondary">Volume (Optional)</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 5"
                  value={volume}
                  onChange={(e) => setVolume(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary text-sm focus-ring placeholder:text-text-muted"
                />
              </div>
            </div>
          </div>
        )}

        {mediaType === 'GAME' && (
          <div className="flex flex-col gap-3 p-3.5 rounded-lg bg-surface-2/40 border border-border-neutral">
            <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
              <Gamepad2 className="w-4 h-4 text-amber-400" />
              <span>Video Game Playtime & Completion</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-text-secondary">Hours Played</label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={hoursPlayed}
                  onChange={(e) => setHoursPlayed(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary text-sm focus-ring"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-text-secondary">Platform (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. PC, PS5, Switch"
                  value={platform}
                  onChange={(e) => setPlatform(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary text-sm focus-ring placeholder:text-text-muted"
                />
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-text-secondary">Completion Type</label>
              <select
                value={completionType}
                onChange={(e) => setCompletionType(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary text-sm focus-ring"
              >
                <option value="">None / Ongoing</option>
                <option value="MAIN_STORY">Main Story</option>
                <option value="MAIN_PLUS_EXTRA">Main Story + Extras</option>
                <option value="COMPLETIONIST">100% Completionist</option>
                <option value="CASUAL">Casual / Endless</option>
                <option value="ABANDONED">Abandoned</option>
              </select>
            </div>
          </div>
        )}

        {/* Modal Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-border-neutral">
          {initialStatus?.id ? (
            <Button
              variant="danger"
              size="sm"
              loading={deleting}
              onClick={handleDelete}
              icon={Trash2}
            >
              Remove
            </Button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onClose} disabled={loading || deleting}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" loading={loading} icon={Check}>
              Save Tracking
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
