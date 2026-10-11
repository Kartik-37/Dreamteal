import React, { useState, useEffect } from 'react';
import { MessageSquare, Trash2, Eye, EyeOff, Globe, Lock, Check } from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { ReactionSelector } from '../../components/reactions/ReactionSelector';
import { ErrorMessage } from '../../components/feedback/ErrorMessage';
import { reviewService } from '../../services/reviews';

/**
 * ReviewModal — Modal for creating, editing, and deleting qualitative media reviews.
 * Adheres strictly to the Zero-Star Policy: non-numeric qualitative reaction badges only.
 */
export function ReviewModal({
  isOpen,
  onClose,
  media,
  initialReview = null,
  onSuccess,
}) {
  const [reactionKey, setReactionKey] = useState(
    () => initialReview?.reaction_key || initialReview?.reaction_detail?.key || null
  );
  const [reviewText, setReviewText] = useState(() => initialReview?.review_text || '');
  const [containsSpoilers, setContainsSpoilers] = useState(() => Boolean(initialReview?.contains_spoilers));
  const [isPublic, setIsPublic] = useState(() => initialReview?.is_public !== undefined ? Boolean(initialReview.is_public) : true);

  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  // Sync state whenever opened
  useEffect(() => {
    if (isOpen) {
      setError(null);
      if (initialReview) {
        setReactionKey(
          initialReview.reaction_key ||
          (initialReview.reaction_detail ? initialReview.reaction_detail.key : null) ||
          null
        );
        setReviewText(initialReview.review_text || '');
        setContainsSpoilers(Boolean(initialReview.contains_spoilers));
        setIsPublic(initialReview.is_public !== undefined ? Boolean(initialReview.is_public) : true);
      } else {
        setReactionKey(null);
        setReviewText('');
        setContainsSpoilers(false);
        setIsPublic(true);
      }
    }
  }, [isOpen, initialReview]);

  if (!media) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let savedReview;
      const payload = {
        reaction_key: reactionKey || null,
        review_text: reviewText.trim(),
        contains_spoilers: containsSpoilers,
        is_public: isPublic,
      };

      if (initialReview?.id) {
        savedReview = await reviewService.updateReview(initialReview.id, payload);
      } else {
        savedReview = await reviewService.createReview({
          media_id: media.id,
          ...payload,
        });
      }

      if (onSuccess) {
        onSuccess(savedReview);
      }
      onClose();
    } catch (err) {
      console.error('Failed to save review:', err);
      // Format backend errors nicely
      let msg = err.message || 'Unable to save review. Please try again.';
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
    if (!initialReview?.id) return;
    if (!window.confirm('Are you sure you want to delete this review?')) return;

    setDeleting(true);
    setError(null);

    try {
      await reviewService.deleteReview(initialReview.id);
      if (onSuccess) {
        onSuccess({ deleted: true, id: initialReview.id });
      }
      onClose();
    } catch (err) {
      console.error('Failed to delete review:', err);
      setError(err.message || 'Failed to delete review.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialReview ? `Edit Review: ${media.title}` : `Review: ${media.title}`}
      description="Share your qualitative impressions and verdict badge. Zero stars, purely editorial."
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {/* Qualitative Reaction Verdict */}
        <div className="space-y-2.5">
          <label className="block text-xs font-semibold uppercase tracking-wider text-text-secondary">
            Verdict Reaction <span className="text-text-muted text-[11px] font-normal lowercase">(optional)</span>
          </label>
          <ReactionSelector
            value={reactionKey}
            onChange={(selectedKey) => setReactionKey(selectedKey)}
            disabled={loading || deleting}
          />
          <p className="text-[11px] text-text-muted">
            Choose how this piece of media resonated with you. Text labels with curated color identity.
          </p>
        </div>

        {/* Written Review (Markdown) */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label
              htmlFor="review-notes-textarea"
              className="block text-xs font-semibold uppercase tracking-wider text-text-secondary"
            >
              Qualitative Notes / Critique
            </label>
            <span className="text-[11px] text-text-muted">Markdown supported</span>
          </div>
          <textarea
            id="review-notes-textarea"
            rows={5}
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
            disabled={loading || deleting}
            placeholder="Write your editorial thoughts, memorable scenes, themes, or critique..."
            className="w-full rounded-lg border border-border-neutral bg-surface-2 px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted/60 focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal disabled:opacity-50 transition-colors resize-y min-h-[100px]"
          />
        </div>

        {/* Visibility and Spoilers Flags */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          {/* Spoiler toggle */}
          <button
            type="button"
            onClick={() => setContainsSpoilers(!containsSpoilers)}
            disabled={loading || deleting}
            className={`flex items-start gap-3 p-3 rounded-lg border text-left transition-all ${
              containsSpoilers
                ? 'border-crimson/50 bg-crimson/10 text-crimson'
                : 'border-border-neutral bg-surface-1 text-text-secondary hover:bg-surface-2'
            }`}
          >
            <div className="mt-0.5">
              {containsSpoilers ? <EyeOff className="w-4 h-4 text-crimson" /> : <Eye className="w-4 h-4 text-text-muted" />}
            </div>
            <div>
              <div className="text-xs font-semibold">Contains Spoilers</div>
              <div className="text-[11px] text-text-muted leading-tight">
                Mask review text behind an explicit reveal click.
              </div>
            </div>
          </button>

          {/* Public vs Private toggle */}
          <button
            type="button"
            onClick={() => setIsPublic(!isPublic)}
            disabled={loading || deleting}
            className={`flex items-start gap-3 p-3 rounded-lg border text-left transition-all ${
              isPublic
                ? 'border-teal/50 bg-teal/10 text-teal'
                : 'border-border-neutral bg-surface-1 text-text-secondary hover:bg-surface-2'
            }`}
          >
            <div className="mt-0.5">
              {isPublic ? <Globe className="w-4 h-4 text-teal" /> : <Lock className="w-4 h-4 text-text-muted" />}
            </div>
            <div>
              <div className="text-xs font-semibold">{isPublic ? 'Public Review' : 'Private Notes'}</div>
              <div className="text-[11px] text-text-muted leading-tight">
                {isPublic ? 'Visible to community visitors.' : 'Visible only to you.'}
              </div>
            </div>
          </button>
        </div>

        {/* Actions bar */}
        <div className="flex items-center justify-between pt-4 border-t border-border-neutral">
          {initialReview ? (
            <Button
              type="button"
              variant="ghost"
              onClick={handleDelete}
              disabled={loading || deleting}
              className="text-crimson hover:bg-crimson/10 hover:text-crimson text-xs"
            >
              <Trash2 className="w-3.5 h-3.5 mr-1.5" />
              {deleting ? 'Deleting...' : 'Delete Review'}
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
              disabled={loading || deleting}
            >
              {loading ? (
                'Saving...'
              ) : (
                <>
                  <Check className="w-4 h-4 mr-1.5" />
                  {initialReview ? 'Save Changes' : 'Publish Review'}
                </>
              )}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
