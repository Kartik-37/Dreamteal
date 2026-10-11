import React, { useState, useEffect } from 'react';
import { Calendar, Trash2, Check, RotateCcw, Clock, Tv, BookOpen, Gamepad2, Search } from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { ErrorMessage } from '../../components/feedback/ErrorMessage';
import { trackingService } from '../../services/tracking';
import { catalogService } from '../../services/catalog';

/**
 * DiaryModal — History-preserving consumption session logger.
 * Allows creating, editing, and deleting individual session records without regressing user progress.
 */
export function DiaryModal({
  isOpen,
  onClose,
  media: propMedia = null,
  initialLog = null,
  onSuccess,
}) {
  const [selectedMedia, setSelectedMedia] = useState(propMedia);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const [loggedDate, setLoggedDate] = useState(() => initialLog?.logged_date || new Date().toISOString().split('T')[0]);
  const [isRewatch, setIsRewatch] = useState(() => Boolean(initialLog?.is_rewatch_or_replay));
  const [sessionNotes, setSessionNotes] = useState(() => initialLog?.session_notes || '');
  const [syncProgress, setSyncProgress] = useState(true);

  // Snapshot fields
  const [season, setSeason] = useState(() => initialLog?.progress_snapshot?.season ?? 0);
  const [episode, setEpisode] = useState(() => initialLog?.progress_snapshot?.episode ?? 0);
  const [chapter, setChapter] = useState(() => initialLog?.progress_snapshot?.chapter ?? 0);
  const [volume, setVolume] = useState(() => initialLog?.progress_snapshot?.volume !== undefined && initialLog?.progress_snapshot?.volume !== null ? String(initialLog.progress_snapshot.volume) : '');
  const [sessionHours, setSessionHours] = useState(() => initialLog?.progress_snapshot?.session_hours !== undefined && initialLog?.progress_snapshot?.session_hours !== null ? String(initialLog.progress_snapshot.session_hours) : '1.0');

  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  // Initialize form state
  useEffect(() => {
    if (isOpen) {
      setError(null);
      setSelectedMedia(propMedia);
      setSearchQuery('');
      setSearchResults([]);

      if (initialLog) {
        setLoggedDate(initialLog.logged_date || new Date().toISOString().split('T')[0]);
        setIsRewatch(Boolean(initialLog.is_rewatch_or_replay));
        setSessionNotes(initialLog.session_notes || '');
        setSyncProgress(true);

        const snap = initialLog.progress_snapshot || {};
        setSeason(snap.season ?? 0);
        setEpisode(snap.episode ?? 0);
        setChapter(snap.chapter ?? 0);
        setVolume(snap.volume !== undefined && snap.volume !== null ? String(snap.volume) : '');
        setSessionHours(snap.session_hours !== undefined && snap.session_hours !== null ? String(snap.session_hours) : '1.0');
      } else {
        setLoggedDate(new Date().toISOString().split('T')[0]);
        setIsRewatch(false);
        setSessionNotes('');
        setSyncProgress(true);
        setSeason(0);
        setEpisode(0);
        setChapter(0);
        setVolume('');
        setSessionHours('1.0');
      }
    }
  }, [isOpen, propMedia, initialLog]);

  // Search local media catalog when no media is chosen
  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    setSearchLoading(true);
    try {
      const res = await catalogService.getMediaList({ search: query.trim() });
      const items = res?.results || (Array.isArray(res) ? res : []);
      setSearchResults(items);
    } catch (err) {
      console.warn('Search failed:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  const activeMedia = selectedMedia || (initialLog?.media_item ? {
    id: typeof initialLog.media_item === 'object' ? initialLog.media_item.id : initialLog.media_item,
    title: initialLog.media_title || 'Media Item',
    media_type: initialLog.media_type || 'UNKNOWN',
  } : null);

  const mediaType = activeMedia?.media_type;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!activeMedia) {
      setError('Please select a media item to log this session for.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Build progress snapshot based on media category
      let snapshot = null;
      if (mediaType === 'SERIES') {
        const s = parseInt(season, 10);
        const ep = parseInt(episode, 10);
        if (s < 0 || ep < 0) {
          throw new Error('Season and Episode cannot be negative.');
        }
        snapshot = { season: s, episode: ep };
      } else if (mediaType === 'MANGA') {
        const ch = parseInt(chapter, 10);
        if (ch < 0) {
          throw new Error('Chapter count cannot be negative.');
        }
        const snapObj = { chapter: ch };
        if (volume !== '') {
          const vol = parseInt(volume, 10);
          if (vol < 0) throw new Error('Volume count cannot be negative.');
          snapObj.volume = vol;
        }
        snapshot = snapObj;
      } else if (mediaType === 'GAME') {
        const h = parseFloat(sessionHours);
        if (isNaN(h) || h < 0) {
          throw new Error('Session hours must be a non-negative number.');
        }
        snapshot = { session_hours: h };
      }

      const payload = {
        media_id: activeMedia.id,
        logged_date: loggedDate,
        is_rewatch_or_replay: isRewatch,
        session_notes: sessionNotes.trim(),
        progress_snapshot: snapshot,
        sync_progress: syncProgress,
      };

      let savedLog;
      if (initialLog?.id) {
        savedLog = await trackingService.updateDiaryLog(initialLog.id, payload);
      } else {
        savedLog = await trackingService.createDiaryLog(payload);
      }

      if (onSuccess) {
        onSuccess(savedLog);
      }
      onClose();
    } catch (err) {
      console.error('Failed to save diary log:', err);
      let msg = err.message || 'Unable to save diary log.';
      if (err.data) {
        if (typeof err.data === 'string') msg = err.data;
        else if (err.data.detail) msg = err.data.detail;
        else if (typeof err.data === 'object') {
          const firstErr = Object.values(err.data)[0];
          msg = Array.isArray(firstErr) ? firstErr[0] : String(firstErr);
        }
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!initialLog?.id) return;
    if (!window.confirm('Delete this diary entry? This will permanently remove this session record.')) return;

    setDeleting(true);
    setError(null);

    try {
      await trackingService.deleteDiaryLog(initialLog.id);
      if (onSuccess) {
        onSuccess({ deleted: true, id: initialLog.id });
      }
      onClose();
    } catch (err) {
      console.error('Failed to delete log:', err);
      setError(err.message || 'Failed to delete diary log.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialLog ? `Edit Diary Entry` : `Log Consumption Session`}
      description="Record a specific date you watched, read, or played. Preserves your complete history."
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {/* Media Selector if not pre-provided */}
        {!activeMedia && (
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Select Media Item
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Search media by title..."
                className="w-full pl-9 pr-3.5 py-2 rounded-lg border border-border-neutral bg-surface-2 text-sm text-text-primary focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
              />
            </div>
            {searchLoading && <div className="text-xs text-text-muted py-1">Searching...</div>}
            {searchResults.length > 0 && (
              <div className="max-h-40 overflow-y-auto rounded-lg border border-border-neutral bg-surface-2 divide-y divide-border-neutral/60">
                {searchResults.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setSelectedMedia(item);
                      setSearchResults([]);
                    }}
                    className="w-full px-3 py-2 text-left flex items-center justify-between hover:bg-surface-3 transition-colors text-xs text-text-primary"
                  >
                    <span className="font-medium truncate">{item.title}</span>
                    <span className="text-[10px] uppercase text-text-muted ml-2">{item.media_type}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Selected Media Indicator */}
        {activeMedia && (
          <div className="flex items-center justify-between p-3 rounded-lg bg-surface-2 border border-border-neutral">
            <div>
              <div className="text-xs font-semibold text-text-primary">{activeMedia.title}</div>
              <div className="text-[11px] text-teal uppercase font-mono tracking-wider">{activeMedia.media_type}</div>
            </div>
            {!propMedia && !initialLog && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setSelectedMedia(null)}
                className="text-[11px] text-text-muted"
              >
                Change
              </Button>
            )}
          </div>
        )}

        {/* Date and Rewatch row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label
              htmlFor="diary-logged-date"
              className="block text-xs font-semibold uppercase tracking-wider text-text-secondary"
            >
              Session Date
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
              <input
                id="diary-logged-date"
                type="date"
                value={loggedDate}
                onChange={(e) => setLoggedDate(e.target.value)}
                disabled={loading || deleting}
                className="w-full pl-9 pr-3 py-2 rounded-lg border border-border-neutral bg-surface-2 text-sm text-text-primary focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
              />
            </div>
          </div>

          <div className="flex items-end">
            <button
              type="button"
              onClick={() => setIsRewatch(!isRewatch)}
              disabled={loading || deleting}
              className={`w-full flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg border text-left transition-colors ${
                isRewatch
                  ? 'border-teal/60 bg-teal/10 text-teal'
                  : 'border-border-neutral bg-surface-2 text-text-secondary hover:bg-surface-3'
              }`}
            >
              <RotateCcw className={`w-4 h-4 ${isRewatch ? 'text-teal' : 'text-text-muted'}`} />
              <div className="text-xs font-medium">
                {isRewatch ? 'Rewatch / Re-read / Replay' : 'First Experience'}
              </div>
            </button>
          </div>
        </div>

        {/* Category-Specific Progress Snapshot Controls */}
        {mediaType === 'SERIES' && (
          <div className="p-3.5 rounded-lg border border-border-neutral bg-surface-1 space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-teal">
              <Tv className="w-3.5 h-3.5" />
              Episode Snapshot
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-text-secondary mb-1">Season</label>
                <input
                  type="number"
                  min="0"
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  disabled={loading || deleting}
                  className="w-full px-3 py-1.5 rounded-md border border-border-neutral bg-surface-2 text-sm text-text-primary focus:border-teal focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] text-text-secondary mb-1">Episode</label>
                <input
                  type="number"
                  min="0"
                  value={episode}
                  onChange={(e) => setEpisode(e.target.value)}
                  disabled={loading || deleting}
                  className="w-full px-3 py-1.5 rounded-md border border-border-neutral bg-surface-2 text-sm text-text-primary focus:border-teal focus:outline-none"
                />
              </div>
            </div>
          </div>
        )}

        {mediaType === 'MANGA' && (
          <div className="p-3.5 rounded-lg border border-border-neutral bg-surface-1 space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-teal">
              <BookOpen className="w-3.5 h-3.5" />
              Chapter / Volume Snapshot
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-text-secondary mb-1">Chapter</label>
                <input
                  type="number"
                  min="0"
                  value={chapter}
                  onChange={(e) => setChapter(e.target.value)}
                  disabled={loading || deleting}
                  className="w-full px-3 py-1.5 rounded-md border border-border-neutral bg-surface-2 text-sm text-text-primary focus:border-teal focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] text-text-secondary mb-1">Volume (optional)</label>
                <input
                  type="number"
                  min="0"
                  value={volume}
                  onChange={(e) => setVolume(e.target.value)}
                  disabled={loading || deleting}
                  placeholder="Optional"
                  className="w-full px-3 py-1.5 rounded-md border border-border-neutral bg-surface-2 text-sm text-text-primary focus:border-teal focus:outline-none"
                />
              </div>
            </div>
          </div>
        )}

        {mediaType === 'GAME' && (
          <div className="p-3.5 rounded-lg border border-border-neutral bg-surface-1 space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-teal">
              <Gamepad2 className="w-3.5 h-3.5" />
              Gameplay Session Hours
            </div>
            <div>
              <label className="block text-[11px] text-text-secondary mb-1">Hours logged in this session</label>
              <input
                type="number"
                step="0.5"
                min="0"
                value={sessionHours}
                onChange={(e) => setSessionHours(e.target.value)}
                disabled={loading || deleting}
                className="w-full px-3 py-1.5 rounded-md border border-border-neutral bg-surface-2 text-sm text-text-primary focus:border-teal focus:outline-none"
              />
              <p className="text-[11px] text-text-muted mt-1">
                The backend `GameSessionTrackingService` automatically credits this duration without double-counting.
              </p>
            </div>
          </div>
        )}

        {/* Forward Sync checkbox */}
        <label className="flex items-center gap-2.5 text-xs text-text-secondary cursor-pointer pt-1">
          <input
            type="checkbox"
            checked={syncProgress}
            onChange={(e) => setSyncProgress(e.target.checked)}
            disabled={loading || deleting}
            className="w-4 h-4 rounded border-border-neutral text-teal focus:ring-teal"
          />
          <span>Forward-sync progress to your active media tracker (never regresses)</span>
        </label>

        {/* Session Notes */}
        <div className="space-y-1.5">
          <label
            htmlFor="diary-session-notes"
            className="block text-xs font-semibold uppercase tracking-wider text-text-secondary"
          >
            Session Notes <span className="text-text-muted text-[11px] font-normal lowercase">(optional)</span>
          </label>
          <textarea
            id="diary-session-notes"
            rows={3}
            value={sessionNotes}
            onChange={(e) => setSessionNotes(e.target.value)}
            disabled={loading || deleting}
            placeholder="What happened in this session? Thoughts, feelings, or milestones..."
            className="w-full rounded-lg border border-border-neutral bg-surface-2 px-3 py-2 text-sm text-text-primary placeholder:text-text-muted/60 focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
          />
        </div>

        {/* Actions bar */}
        <div className="flex items-center justify-between pt-4 border-t border-border-neutral">
          {initialLog ? (
            <Button
              type="button"
              variant="ghost"
              onClick={handleDelete}
              disabled={loading || deleting}
              className="text-crimson hover:bg-crimson/10 text-xs"
            >
              <Trash2 className="w-3.5 h-3.5 mr-1.5" />
              {deleting ? 'Deleting...' : 'Delete Log'}
            </Button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2.5">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading || deleting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={loading || deleting || !activeMedia}
            >
              {loading ? (
                'Saving...'
              ) : (
                <>
                  <Check className="w-4 h-4 mr-1.5" />
                  {initialLog ? 'Save Entry' : 'Log to Diary'}
                </>
              )}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
