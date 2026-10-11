import { test, expect, describe } from 'vitest';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';

import { SafeMarkdown } from '../components/ui/SafeMarkdown.jsx';
import { TrackingModal } from '../features/tracking/TrackingModal.jsx';
import { ReviewModal } from '../features/reviews/ReviewModal.jsx';
import { DiaryModal } from '../features/diary/DiaryModal.jsx';
import { CollectionsPage } from '../features/collections/CollectionsPage.jsx';
import { LoginPage } from '../features/auth/LoginPage.jsx';
import { AuthProvider } from '../features/auth/AuthContext.jsx';
import { REACTION_LIST } from '../utils/constants.js';

describe('Phase 5 Interactive UX & Core Component Tests', () => {
  describe('SafeMarkdown Sanitization & Formatting', () => {
    test('renders basic markdown syntax safely (bold, italic, code, quote)', () => {
      const content = '**Bold Title**\n\n*Italic text* with `code block`\n\n> Blockquote text';
      const html = renderToString(<SafeMarkdown content={content} />);
      expect(html).toContain('Bold Title');
      expect(html).toContain('Italic text');
      expect(html).toContain('code block');
      expect(html).toContain('Blockquote text');
      expect(html).toContain('<strong');
      expect(html).toContain('<em');
      expect(html).toContain('<code');
      expect(html).toContain('<blockquote');
    });

    test('escapes raw HTML tags to prevent XSS injection', () => {
      const malicious = '<script>alert("xss")</script><img src=x onerror=alert(1)>';
      const html = renderToString(<SafeMarkdown content={malicious} />);
      expect(html).not.toContain('<script>');
      expect(html).not.toContain('<img');
      expect(html).toContain('&lt;script&gt;');
      expect(html).toContain('&lt;img');
    });
  });

  describe('TrackingModal Verification', () => {
    test('renders series-specific episode controls without star ratings', () => {
      const seriesMedia = {
        id: '11111111-1111-1111-1111-111111111111',
        title: 'Breaking Bad',
        media_type: 'SERIES',
        slug: 'breaking-bad',
      };
      const html = renderToString(
        <TrackingModal
          isOpen={true}
          onClose={() => {}}
          media={seriesMedia}
          initialStatus={{ status: 'WATCHING', is_favorite: true }}
          initialProgress={{ series_progress: { current_season: 2, current_episode: 5 } }}
        />
      );
      expect(html).toContain('Breaking Bad');
      expect(html).toContain('Current Season');
      expect(html).toContain('Current Episode');
      expect(html).not.toContain('★');
      expect(html).not.toContain('⭐');
      expect(html).not.toContain('/ 10');
    });

    test('renders game-specific hours played and platform without star ratings', () => {
      const gameMedia = {
        id: '22222222-2222-2222-2222-222222222222',
        title: 'Elden Ring',
        media_type: 'GAME',
        slug: 'elden-ring',
      };
      const html = renderToString(
        <TrackingModal
          isOpen={true}
          onClose={() => {}}
          media={gameMedia}
          initialStatus={{ status: 'WATCHING' }}
          initialProgress={{ game_progress: { hours_played: '45.5', platform_played_on: 'PC' } }}
        />
      );
      expect(html).toContain('Elden Ring');
      expect(html).toContain('Hours Played');
      expect(html).toContain('Platform');
      expect(html).not.toContain('★');
      expect(html).not.toContain('⭐');
    });
  });

  describe('ReviewModal & Qualitative Reaction Verification', () => {
    test('renders all 5 qualitative verdicts with spoiler and privacy toggles', () => {
      const media = {
        id: '33333333-3333-3333-3333-333333333333',
        title: 'Spirited Away',
        media_type: 'MOVIE',
      };
      const html = renderToString(
        <ReviewModal
          isOpen={true}
          onClose={() => {}}
          media={media}
          initialReview={{
            reaction_key: 'peak',
            review_text: 'A masterpiece.',
            contains_spoilers: false,
            is_public: true,
          }}
        />
      );

      // Verify qualitative reaction badges present
      for (const reaction of REACTION_LIST) {
        expect(html).toContain(reaction.label);
      }
      expect(html).toContain('Contains Spoilers');
      expect(html).toContain('Public Review');
      expect(html).toContain('A masterpiece.');
      // Strictly Zero Stars
      expect(html).not.toContain('★');
      expect(html).not.toContain('⭐');
      expect(html).not.toContain('/ 10');
      expect(html).not.toContain('/ 5');
    });
  });

  describe('DiaryModal Verification', () => {
    test('renders date picker, rewatch toggle, and forward-progress synchronization', () => {
      const media = {
        id: '44444444-4444-4444-4444-444444444444',
        title: 'Chainsaw Man',
        media_type: 'MANGA',
      };
      const html = renderToString(
        <DiaryModal
          isOpen={true}
          onClose={() => {}}
          media={media}
          initialLog={{
            logged_date: '2026-10-11',
            is_rewatch_or_replay: true,
            session_notes: 'Read volume 3.',
            progress_snapshot: { chapter: 22, volume: 3 },
          }}
        />
      );

      expect(html).toContain('Edit Diary Entry');
      expect(html).toContain('Session Date');
      expect(html).toContain('Rewatch / Re-read / Replay');
      expect(html).toContain('Chapter');
      expect(html).toContain('Forward-sync progress');
      expect(html).not.toContain('★');
    });
  });

  describe('CollectionsPage Verification', () => {
    test('renders Phase 6 architectural roadmap without fake localStorage mock', () => {
      const html = renderToString(
        <MemoryRouter>
          <CollectionsPage />
        </MemoryRouter>
      );
      expect(html).toContain('Curated Media Collections');
      expect(html).toContain('Phase 6 Backend Extension Specification');
      expect(html).toContain('apps/collections/');
      expect(html).toContain('does not simulate collections');
    });
  });

  describe('LoginPage Verification', () => {
    test('renders Django session and CSRF security form', () => {
      const html = renderToString(
        <MemoryRouter>
          <AuthProvider>
            <LoginPage />
          </AuthProvider>
        </MemoryRouter>
      );
      expect(html).toContain('Sign In to DreamTeal');
      expect(html).toContain('Django Session &amp; CSRF Security');
      expect(html).toContain('Username');
      expect(html).toContain('Password');
    });
  });
});
