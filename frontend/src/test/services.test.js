import { test, expect, describe, vi } from 'vitest';

import { authService } from '../services/auth.js';
import { catalogService } from '../services/catalog.js';
import { trackingService } from '../services/tracking.js';
import { reviewService } from '../services/reviews.js';
import { recommendationService } from '../services/recommendations.js';

describe('Feature Services Contract Verification', () => {
  test('authService methods call correct backend endpoints', async () => {
    let captured = null;
    const originalFetch = globalThis.fetch;
    globalThis.fetch = vi.fn(async (url, options) => {
      captured = { url, options };
      return {
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => ({ user: { id: 1, username: 'tester' } }),
      };
    });

    try {
      await authService.login('tester', 'password123');
      expect(captured.url).toContain('/api/v1/users/login/');
      expect(captured.options.method).toBe('POST');
      expect(captured.options.body).toContain('tester');

      await authService.getCurrentUser();
      expect(captured.url).toContain('/api/v1/users/me/');
      expect(captured.options.method).toBe('GET');

      await authService.logout();
      expect(captured.url).toContain('/api/v1/users/logout/');
      expect(captured.options.method).toBe('POST');
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test('catalogService methods call correct catalog endpoints', async () => {
    let captured = null;
    const originalFetch = globalThis.fetch;
    globalThis.fetch = vi.fn(async (url, options) => {
      captured = { url, options };
      return {
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => ({ results: [] }),
      };
    });

    try {
      await catalogService.getMediaList({ category: 'MOVIE' });
      expect(captured.url).toContain('/api/v1/media/');
      expect(captured.url).toContain('category=MOVIE');

      await catalogService.getMediaDetail('severance-2022');
      expect(captured.url).toContain('/api/v1/media/severance-2022/');

      await catalogService.searchMedia({ q: 'Batman' });
      expect(captured.url).toContain('/api/v1/media/search/?q=Batman');

      await catalogService.getDiscovery('movies', { mode: 'trending' });
      expect(captured.url).toContain('/api/v1/discovery/movies/?mode=trending');
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test('recommendationService calls deterministic recommendation endpoint', async () => {
    let captured = null;
    const originalFetch = globalThis.fetch;
    globalThis.fetch = vi.fn(async (url, options) => {
      captured = { url, options };
      return {
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => ({ recommendations: [] }),
      };
    });

    try {
      await recommendationService.getNext('severance-2022', { limit: 5 });
      expect(captured.url).toContain('/api/v1/recommendations/next/severance-2022/');
      expect(captured.url).toContain('limit=5');
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test('reviewService & trackingService call correct review and tracking endpoints', async () => {
    let captured = null;
    const originalFetch = globalThis.fetch;
    globalThis.fetch = vi.fn(async (url, options) => {
      captured = { url, options };
      return {
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => ({ id: 'uuid-1' }),
      };
    });

    try {
      await reviewService.getReactions();
      expect(captured.url).toContain('/api/v1/reviews/reactions/');

      await trackingService.createStatus({ media_id: 'uuid-1', status: 'WATCHING' });
      expect(captured.url).toContain('/api/v1/tracking/status/');
      expect(captured.options.method).toBe('POST');

      await trackingService.getDiaryLogs({ year: 2026 });
      expect(captured.url).toContain('/api/v1/tracking/logs/?year=2026');
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
