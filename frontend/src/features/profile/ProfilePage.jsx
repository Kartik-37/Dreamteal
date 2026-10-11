import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  User, Mail, Edit3, Check, Bookmark, Calendar, Heart, Film,
  Tv, BookOpen, Gamepad2, ShieldCheck, Flame, Sparkles
} from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { authService } from '../../services/auth';
import { trackingService } from '../../services/tracking';
import { reviewService } from '../../services/reviews';
import { Button } from '../../components/ui/Button';
import { ReactionBadge } from '../../components/reactions/ReactionBadge';
import { LoadingSpinner } from '../../components/feedback/LoadingSpinner';
import { ErrorMessage } from '../../components/feedback/ErrorMessage';
import { EmptyState } from '../../components/feedback/EmptyState';
import { REACTIONS, REACTION_LIST, TRACKING_STATUSES } from '../../utils/constants';

export function ProfilePage() {
  const { user, isAuthenticated, refreshUser } = useAuth();
  const navigate = useNavigate();

  // Profile edit states
  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [bio, setBio] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState(null);

  // Engagement states
  const [statuses, setStatuses] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [recentLogs, setRecentLogs] = useState([]);
  const [loadingData, setLoadingData] = useState(true);

  // Initialize edit form
  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || user.username || '');
      setBio(user.bio || '');
    }
  }, [user]);

  const loadUserData = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoadingData(true);
    try {
      // 1. Load tracking statuses
      const statusRes = await trackingService.getStatuses();
      const statusList = statusRes?.results || (Array.isArray(statusRes) ? statusRes : []);
      setStatuses(statusList);

      // 2. Load reviews for qualitative reaction breakdown
      const revRes = await reviewService.getReviews();
      const revList = revRes?.results || (Array.isArray(revRes) ? revRes : []);
      // Filter to current user
      const userRevs = revList.filter((r) => r.user === user?.id || r.username === user?.username);
      setReviews(userRevs);

      // 3. Load recent diary logs
      const diaryRes = await trackingService.getDiaryLogs();
      const diaryList = diaryRes?.results || (Array.isArray(diaryRes) ? diaryRes : []);
      setRecentLogs(diaryList.slice(0, 5));
    } catch (err) {
      console.warn('Failed to load user engagement data:', err);
    } finally {
      setLoadingData(false);
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    loadUserData();
  }, [loadUserData]);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileError(null);
    try {
      await authService.updateProfile({
        display_name: displayName.trim(),
        bio: bio.trim(),
      });
      await refreshUser();
      setIsEditing(false);
    } catch (err) {
      setProfileError(err.message || 'Failed to update profile.');
    } finally {
      setSavingProfile(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center space-y-6">
        <div className="w-16 h-16 rounded-full bg-surface-2 border border-border-neutral flex items-center justify-center mx-auto text-text-muted">
          <User className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-serif text-text-primary">Sign in to view your profile</h1>
        <p className="text-sm text-text-secondary">
          Track movies, series, manga, and games, view your qualitative reaction breakdown, and access your consumption diary.
        </p>
        <Button variant="primary" onClick={() => navigate('/login')}>
          Sign In
        </Button>
      </div>
    );
  }

  // Tally qualitative reaction counts (Strictly non-numeric)
  const reactionCounts = {};
  for (const r of REACTION_LIST) {
    reactionCounts[r.key] = 0;
  }
  for (const rev of reviews) {
    const k = rev.reaction_key || rev.reaction_detail?.key;
    if (k && reactionCounts[k] !== undefined) {
      reactionCounts[k] += 1;
    }
  }

  // Status breakdown
  const statusCounts = {
    WATCHING: 0,
    COMPLETED: 0,
    ON_HOLD: 0,
    DROPPED: 0,
    PLAN_TO_WATCH: 0,
  };
  let favoritesCount = 0;
  for (const st of statuses) {
    if (statusCounts[st.status] !== undefined) {
      statusCounts[st.status] += 1;
    }
    if (st.is_favorite) favoritesCount += 1;
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-10">
      {/* Profile Header Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-surface-1 border border-border-neutral space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-teal/10 border-2 border-teal/40 flex items-center justify-center text-teal shrink-0">
              <User className="w-8 h-8 sm:w-10 sm:h-10" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h1 className="text-2xl sm:text-3xl font-serif font-bold text-text-primary">
                  {user.display_name || user.username}
                </h1>
                {user.is_staff && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-electric-gold/10 text-electric-gold border border-electric-gold/30">
                    Staff
                  </span>
                )}
              </div>
              <div className="text-xs text-text-muted font-mono flex items-center gap-1.5">
                <span>@{user.username}</span>
                {user.email && (
                  <>
                    <span>•</span>
                    <span>{user.email}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsEditing(!isEditing)}
            className="self-start text-xs"
          >
            <Edit3 className="w-3.5 h-3.5 mr-1.5" />
            {isEditing ? 'Cancel Edit' : 'Edit Profile'}
          </Button>
        </div>

        {/* Bio or Edit Form */}
        {isEditing ? (
          <form onSubmit={handleSaveProfile} className="space-y-4 pt-4 border-t border-border-neutral">
            {profileError && <ErrorMessage message={profileError} onDismiss={() => setProfileError(null)} />}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-text-secondary">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border-neutral bg-surface-2 text-sm text-text-primary focus:border-teal focus:outline-none"
              />
            </div>
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-text-secondary">
                Bio
              </label>
              <textarea
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Share a bit about your media interests..."
                className="w-full px-3 py-2 rounded-lg border border-border-neutral bg-surface-2 text-sm text-text-primary focus:border-teal focus:outline-none resize-y"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setIsEditing(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={savingProfile}>
                {savingProfile ? 'Saving...' : 'Save Profile'}
              </Button>
            </div>
          </form>
        ) : (
          user.bio && (
            <p className="text-sm text-text-secondary leading-relaxed max-w-2xl pt-2 border-t border-border-neutral/60">
              {user.bio}
            </p>
          )
        )}
      </div>

      {/* Qualitative Reaction Breakdown (Zero Stars Policy) */}
      <div className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-lg sm:text-xl font-serif font-bold text-text-primary flex items-center gap-2">
            <Flame className="w-5 h-5 text-teal" />
            Qualitative Reaction Breakdown
          </h2>
          <p className="text-xs text-text-secondary">
            Universal qualitative verdict distribution across all your authored media reviews. Strictly non-numeric.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {REACTION_LIST.map((r) => (
            <div
              key={r.key}
              className="p-4 rounded-xl border flex flex-col items-center text-center space-y-2 transition-all"
              style={{
                backgroundColor: r.bg,
                borderColor: r.border,
              }}
            >
              <ReactionBadge reactionKey={r.key} size="sm" />
              <div
                className="text-2xl sm:text-3xl font-bold font-mono tracking-tight"
                style={{ color: r.color }}
              >
                {reactionCounts[r.key] || 0}
              </div>
              <span className="text-[10px] uppercase font-mono text-text-muted">
                Reviews
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Tracking Status Breakdown */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-lg sm:text-xl font-serif font-bold text-text-primary flex items-center gap-2">
              <Bookmark className="w-5 h-5 text-teal" />
              Media Tracking Overview
            </h2>
            <p className="text-xs text-text-secondary">
              Summary of your tracked catalog items across all categories.
            </p>
          </div>
          <Link
            to="/discovery"
            className="text-xs text-teal hover:underline font-medium"
          >
            Explore Catalog →
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-4 rounded-xl bg-surface-1 border border-border-neutral text-center space-y-1">
            <div className="text-xl sm:text-2xl font-bold font-mono text-teal">
              {statusCounts.WATCHING}
            </div>
            <div className="text-[11px] uppercase font-semibold text-text-muted">Active / In Progress</div>
          </div>

          <div className="p-4 rounded-xl bg-surface-1 border border-border-neutral text-center space-y-1">
            <div className="text-xl sm:text-2xl font-bold font-mono text-radiant-teal">
              {statusCounts.COMPLETED}
            </div>
            <div className="text-[11px] uppercase font-semibold text-text-muted">Completed</div>
          </div>

          <div className="p-4 rounded-xl bg-surface-1 border border-border-neutral text-center space-y-1">
            <div className="text-xl sm:text-2xl font-bold font-mono text-electric-gold">
              {statusCounts.PLAN_TO_WATCH}
            </div>
            <div className="text-[11px] uppercase font-semibold text-text-muted">Plan to Watch/Play</div>
          </div>

          <div className="p-4 rounded-xl bg-surface-1 border border-border-neutral text-center space-y-1">
            <div className="text-xl sm:text-2xl font-bold font-mono text-muted-lavender">
              {statusCounts.ON_HOLD}
            </div>
            <div className="text-[11px] uppercase font-semibold text-text-muted">On Hold</div>
          </div>

          <div className="p-4 rounded-xl bg-surface-1 border border-border-neutral text-center space-y-1">
            <div className="text-xl sm:text-2xl font-bold font-mono text-crimson">
              {statusCounts.DROPPED}
            </div>
            <div className="text-[11px] uppercase font-semibold text-text-muted">Dropped</div>
          </div>

          <div className="p-4 rounded-xl bg-surface-1 border border-border-neutral text-center space-y-1">
            <div className="text-xl sm:text-2xl font-bold font-mono text-warm-coral">
              {favoritesCount}
            </div>
            <div className="text-[11px] uppercase font-semibold text-text-muted">Favorites</div>
          </div>
        </div>
      </div>

      {/* Recent Diary Activity Section */}
      <div className="space-y-4 pt-2">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-lg sm:text-xl font-serif font-bold text-text-primary flex items-center gap-2">
              <Calendar className="w-5 h-5 text-teal" />
              Recent Consumption Logs
            </h2>
            <p className="text-xs text-text-secondary">
              Latest activity from your history-preserving consumption diary.
            </p>
          </div>
          <Link
            to="/diary"
            className="text-xs text-teal hover:underline font-medium"
          >
            Full Diary Timeline →
          </Link>
        </div>

        {recentLogs.length === 0 ? (
          <div className="p-6 rounded-xl bg-surface-1 border border-border-neutral text-center">
            <p className="text-xs text-text-muted">No sessions logged yet.</p>
            <Link to="/diary" className="inline-block mt-2 text-xs text-teal hover:underline">
              Log your first session in the Diary
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-border-neutral/60 rounded-xl bg-surface-1 border border-border-neutral overflow-hidden">
            {recentLogs.map((log) => (
              <div key={log.id} className="p-3.5 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-text-muted">
                    {log.logged_date}
                  </span>
                  <span className="font-medium text-text-primary">
                    {log.media_title || 'Media Item'}
                  </span>
                </div>
                {log.is_rewatch_or_replay && (
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-surface-2 text-teal border border-border-neutral">
                    Rewatch
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
