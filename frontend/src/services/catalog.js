/**
 * DreamTeal Catalog & Discovery Service
 */

import { apiClient } from './api';

export const catalogService = {
  /**
   * Browse media catalog.
   * @param {object} params - { category, search, genre, tag, ordering, page }
   */
  async getMediaList(params = {}) {
    return apiClient('/api/v1/media/', {
      method: 'GET',
      params,
    });
  },

  /**
   * Get single media item details by slug.
   * @param {string} slug
   */
  async getMediaDetail(slug) {
    return apiClient(`/api/v1/media/${encodeURIComponent(slug)}/`, {
      method: 'GET',
    });
  },

  /**
   * Search across external metadata providers.
   * @param {object} params - { q, category, limit }
   */
  async searchMedia(params = {}) {
    return apiClient('/api/v1/media/search/', {
      method: 'GET',
      params,
    });
  },

  /**
   * Multi-mode discovery feeds (movies, series, manga, manhwa, games).
   * @param {string} category - 'movies' | 'series' | 'manga' | 'manhwa' | 'games'
   * @param {object} params - { mode: 'popular' | 'latest' | 'trending' | 'upcoming', limit }
   */
  async getDiscovery(category, params = {}) {
    return apiClient(`/api/v1/discovery/${encodeURIComponent(category)}/`, {
      method: 'GET',
      params,
    });
  },

  /**
   * List active external metadata providers and attribution notices.
   */
  async getProviders() {
    return apiClient('/api/v1/catalog/providers/', {
      method: 'GET',
    });
  },

  /**
   * On-demand import of external media items into catalog.
   */
  async importMedia(importData) {
    return apiClient('/api/v1/media/import/', {
      method: 'POST',
      body: importData,
    });
  },
};
