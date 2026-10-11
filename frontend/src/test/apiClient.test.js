import { test, expect, describe, vi } from 'vitest';

import {
  ApiError,
  setCachedCsrfToken,
  apiClient,
} from '../services/api.js';

describe('Central API Client & Normalized Error Handling', () => {
  test('ApiError correctly identifies HTTP status types', () => {
    const authErr401 = new ApiError('Unauthorized', { status: 401 });
    expect(authErr401.isAuthError).toBe(true);
    expect(authErr401.isNotFound).toBe(false);

    const authErr403 = new ApiError('Forbidden', { status: 403 });
    expect(authErr403.isAuthError).toBe(true);

    const notFoundErr = new ApiError('Not found', { status: 404 });
    expect(notFoundErr.isNotFound).toBe(true);
    expect(notFoundErr.isAuthError).toBe(false);

    const conflictErr = new ApiError('Conflict', { status: 409 });
    expect(conflictErr.isConflict).toBe(true);

    const validationErr = new ApiError('Bad Request', { status: 400 });
    expect(validationErr.isValidationError).toBe(true);

    const netErr = new ApiError('Failed to fetch', { isNetwork: true });
    expect(netErr.isNetwork).toBe(true);
  });

  test('apiClient attaches X-CSRFToken and credentials:include for unsafe methods', async () => {
    let capturedUrl = null;
    let capturedOptions = null;

    const originalFetch = globalThis.fetch;
    globalThis.fetch = vi.fn(async (url, options) => {
      capturedUrl = url;
      capturedOptions = options;
      return {
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => ({ success: true }),
      };
    });

    try {
      setCachedCsrfToken('test-csrf-token-12345');

      // Safe GET method does not attach X-CSRFToken
      await apiClient('/api/v1/media/');
      expect(capturedOptions.method).toBe('GET');
      expect(capturedOptions.credentials).toBe('include');
      expect(capturedOptions.headers['X-CSRFToken']).toBeUndefined();

      // Unsafe POST method attaches X-CSRFToken
      await apiClient('/api/v1/tracking/status/', {
        method: 'POST',
        body: { status: 'WATCHING' },
      });
      expect(capturedOptions.method).toBe('POST');
      expect(capturedOptions.credentials).toBe('include');
      expect(capturedOptions.headers['X-CSRFToken']).toBe('test-csrf-token-12345');
      expect(capturedOptions.headers['Content-Type']).toBe('application/json');

      // Unsafe PATCH method attaches X-CSRFToken
      await apiClient('/api/v1/tracking/status/1/', {
        method: 'PATCH',
        body: { is_favorite: true },
      });
      expect(capturedOptions.method).toBe('PATCH');
      expect(capturedOptions.headers['X-CSRFToken']).toBe('test-csrf-token-12345');

      // Unsafe DELETE method attaches X-CSRFToken
      await apiClient('/api/v1/tracking/logs/1/', {
        method: 'DELETE',
      });
      expect(capturedOptions.method).toBe('DELETE');
      expect(capturedOptions.headers['X-CSRFToken']).toBe('test-csrf-token-12345');
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test('apiClient serializes query parameters correctly', async () => {
    let capturedUrl = null;
    const originalFetch = globalThis.fetch;
    globalThis.fetch = vi.fn(async (url) => {
      capturedUrl = url;
      return {
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => ({ results: [] }),
      };
    });

    try {
      await apiClient('/api/v1/media/', {
        params: { category: 'MOVIE', search: 'Batman', page: 1 },
      });
      expect(capturedUrl).toContain('category=MOVIE');
      expect(capturedUrl).toContain('search=Batman');
      expect(capturedUrl).toContain('page=1');
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
