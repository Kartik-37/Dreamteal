/**
 * DreamTeal Deterministic Recommendation Service
 */

import { apiClient } from './api';

export const recommendationService = {
  /**
   * Get deterministic "What to consume next" recommendations based on a media item.
   * @param {string} slug - Base media slug
   * @param {object} params - { cross_category, category, limit }
   */
  async getNext(slug, params = {}) {
    return apiClient(`/api/v1/recommendations/next/${encodeURIComponent(slug)}/`, {
      method: 'GET',
      params,
    });
  },
};
