import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Plus, BookOpen, RotateCcw, Edit2, Trash2, Clock, Film, Tv, Gamepad2, ShieldAlert } from 'lucide-react';
import { trackingService } from '../../services/tracking';
import { useAuth } from '../auth/AuthContext';
import { Button } from '../../components/ui/Button';
import { DiaryModal } from './DiaryModal';
import { LoadingSpinner } from '../../components/feedback/LoadingSpinner';
import { EmptyState } from '../../components/feedback/EmptyState';
import { ErrorMessage } from '../../components/feedback/ErrorMessage';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export function DiaryPage() {
  const { isAuthenticated, user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter states
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedMonth, setSelectedMonth] = useState('');

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingLog, setEditingLog] = useState(null);

  const fetchLogs = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (selectedYear) params.year = parseInt(selectedYear, 10);
      if (selectedMonth) params.month = parseInt(selectedMonth, 10);

      const res = await trackingService.getDiaryLogs(params);
      const items = res?.results || (Array.isArray(res) ? res : []);
      setLogs(items);
    } catch (err) {
      console.error('Failed to fetch diary logs:', err);
      setError(err.message || 'Unable to load diary history. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, selectedYear, selectedMonth]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleOpenCreate = () => {
    setEditingLog(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (log) => {
    setEditingLog(log);
    setIsModalOpen(true);
  };

  const handleModalSuccess = () => {
    fetchLogs();
  };

  const handleDelete = async (logId) => {
    if (!window.confirm('Delete this diary entry? This action cannot be undone.')) return;
    try {
      await trackingService.deleteDiaryLog(logId);
      setLogs((prev) => prev.filter((l) => l.id !== logId));
    } catch (err) {
      alert(err.message || 'Failed to delete log entry.');
    }
  };

  // Group logs chronologically by Year, then Month
  const groupedLogs = useMemo(() => {
    const groups = {};
    for (const log of logs) {
      if (!log.logged_date) continue;
      const parts = log.logged_date.split('-');
      const year = parts[0] || 'Unknown Year';
      const monthNum = parseInt(parts[1], 10);
      const monthName = !isNaN(monthNum) && monthNum >= 1 && monthNum <= 12
        ? MONTH_NAMES[monthNum - 1]
        : 'Unknown Month';

      const key = `${year} — ${monthName}`;
      if (!groups[key]) {
        groups[key] = {
          year,
          monthName,
          items: [],
        };
      }
      groups[key].items.push(log);
    }
    return groups;
  }, [logs]);

  // Extract available years for filter
  const availableYears = useMemo(() => {
    const years = new Set();
    const currentYear = new Date().getFullYear();
    years.add(currentYear);
    for (const log of logs) {
      if (log.logged_date) {
        years.add(parseInt(log.logged_date.split('-')[0], 10));
      }
    }
    return Array.from(years).sort((a, b) => b - a);
  }, [logs]);

  const renderProgressSnapshot = (log) => {
    const snap = log.progress_snapshot;
    if (!snap) return null;

    if (snap.season !== undefined && snap.episode !== undefined) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-2 text-teal font-mono text-xs border border-border-neutral">
          <Tv className="w-3 h-3" />
          S{snap.season}E{snap.episode}
        </span>
      );
    }
    if (snap.chapter !== undefined) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-2 text-warm-coral font-mono text-xs border border-border-neutral">
          <BookOpen className="w-3 h-3" />
          Ch. {snap.chapter}
          {snap.volume ? ` (Vol. ${snap.volume})` : ''}
        </span>
      );
    }
    if (snap.session_hours !== undefined) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-2 text-electric-gold font-mono text-xs border border-border-neutral">
          <Gamepad2 className="w-3 h-3" />
          {snap.session_hours}h session
        </span>
      );
    }
    return null;
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-6">
        <div className="w-16 h-16 rounded-full bg-teal/10 border border-teal/30 flex items-center justify-center mx-auto text-teal">
          <Calendar className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-serif text-text-primary">Consumption Diary</h1>
          <p className="text-text-secondary max-w-md mx-auto text-sm leading-relaxed">
            Your personal chronological timeline of movies watched, series caught up on, manga chapters read, and games played.
          </p>
        </div>
        <div className="p-6 max-w-sm mx-auto rounded-xl bg-surface-1 border border-border-neutral text-left space-y-4">
          <p className="text-xs text-text-muted">
            Sign in to start logging your consumption sessions and preserve your chronological media history.
          </p>
          <Button variant="primary" className="w-full" onClick={() => window.location.assign('/login')}>
            Sign In to DreamTeal
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-border-neutral">
        <div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-text-primary tracking-tight">
            Media Diary
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            History-preserving timeline of every film, episode, chapter, and gaming session.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="primary" onClick={handleOpenCreate} className="shadow-sm">
            <Plus className="w-4 h-4 mr-1.5" />
            Log Session
          </Button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3 bg-surface-1 p-3 rounded-lg border border-border-neutral">
        <div className="text-xs font-semibold uppercase tracking-wider text-text-muted flex items-center gap-1.5 pl-1">
          <Calendar className="w-3.5 h-3.5 text-teal" />
          Filter:
        </div>

        {/* Year filter */}
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(e.target.value)}
          className="bg-surface-2 border border-border-neutral rounded-md px-3 py-1.5 text-xs text-text-primary focus:border-teal focus:outline-none"
        >
          <option value="">All Years</option>
          {availableYears.map((yr) => (
            <option key={yr} value={yr}>
              {yr}
            </option>
          ))}
        </select>

        {/* Month filter */}
        <select
          value={selectedMonth}
          onChange={(e) => setSelectedMonth(e.target.value)}
          className="bg-surface-2 border border-border-neutral rounded-md px-3 py-1.5 text-xs text-text-primary focus:border-teal focus:outline-none"
        >
          <option value="">All Months</option>
          {MONTH_NAMES.map((name, idx) => (
            <option key={name} value={idx + 1}>
              {name}
            </option>
          ))}
        </select>

        {(selectedYear || selectedMonth) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSelectedYear('');
              setSelectedMonth('');
            }}
            className="text-xs text-text-muted hover:text-text-primary ml-auto"
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Error state */}
      {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

      {/* Loading state */}
      {loading && (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" />
          <p className="text-xs text-text-muted">Loading your consumption diary...</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && logs.length === 0 && (
        <EmptyState
          title="No diary entries logged"
          message={
            selectedYear || selectedMonth
              ? "No entries found for the selected period."
              : "You haven't logged any media sessions yet. Start your journey by clicking 'Log Session'."
          }
          actionLabel="Log First Session"
          onAction={handleOpenCreate}
        />
      )}

      {/* Chronological Timeline */}
      {!loading && logs.length > 0 && (
        <div className="space-y-10">
          {Object.entries(groupedLogs).map(([groupKey, group]) => (
            <div key={groupKey} className="space-y-4">
              <div className="sticky top-16 z-10 py-2 bg-background-deep/90 backdrop-blur-md border-b border-border-neutral flex items-center justify-between">
                <h2 className="text-base sm:text-lg font-serif font-bold text-teal tracking-wide">
                  {group.monthName} {group.year}
                </h2>
                <span className="text-xs font-mono text-text-muted">
                  {group.items.length} {group.items.length === 1 ? 'entry' : 'entries'}
                </span>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {group.items.map((log) => {
                  const mediaTitle = log.media_title || 'Media Item';
                  return (
                    <div
                      key={log.id}
                      className="group relative flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-surface-1 border border-border-neutral hover:border-teal/50 hover:bg-surface-2/60 transition-all duration-200 gap-3"
                    >
                      <div className="flex items-start sm:items-center gap-3.5 min-w-0">
                        {/* Date badge */}
                        <div className="flex flex-col items-center justify-center w-12 h-12 rounded-lg bg-surface-2 border border-border-neutral shrink-0 text-center font-mono">
                          <span className="text-[10px] uppercase text-text-muted leading-tight">
                            {log.logged_date ? new Date(log.logged_date).toLocaleString('en', { month: 'short' }) : '---'}
                          </span>
                          <span className="text-sm font-bold text-text-primary leading-tight">
                            {log.logged_date ? log.logged_date.split('-')[2] : '--'}
                          </span>
                        </div>

                        {/* Details */}
                        <div className="min-w-0 space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold text-text-primary text-sm truncate">
                              {mediaTitle}
                            </span>

                            {renderProgressSnapshot(log)}

                            {log.is_rewatch_or_replay && (
                              <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-surface-2 text-text-muted border border-border-neutral">
                                <RotateCcw className="w-2.5 h-2.5 text-teal" />
                                Rewatch
                              </span>
                            )}
                          </div>

                          {log.session_notes && (
                            <p className="text-xs text-text-secondary line-clamp-2 italic pr-2">
                              "{log.session_notes}"
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Item Actions */}
                      <div className="flex items-center gap-1 self-end sm:self-center shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenEdit(log)}
                          className="h-8 w-8 p-0 text-text-muted hover:text-text-primary"
                          title="Edit log entry"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(log.id)}
                          className="h-8 w-8 p-0 text-text-muted hover:text-crimson"
                          title="Delete log entry"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Diary Modal */}
      <DiaryModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialLog={editingLog}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
}
