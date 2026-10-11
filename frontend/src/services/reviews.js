/**
 * DreamTeal Qualitative Review & Reaction Service
 */

import { apiClient } from './api';

export const reviewService = {
  /**
   * Fetch approved universal qualitative reactions taxonomy.
   */
  async getReactions() {
    return apiClient('/api/v1/reviews/reactions/', {
      method: 'GET',
    });
  },

  /**
   * Create a qualitative review with reaction verdict.
   */
  async createReview(reviewData) {
    return apiClient('/api/v1/reviews/', {
      method: 'POST',
      body: reviewData,
    });
  },

  /**
   * Get single review by ID.
   */
  async getReview(reviewId) {
    return apiClient(`/api/v1/reviews/${encodeURIComponent(reviewId)}/`, {
      method: 'GET',
    });
  },

  /**
   * Update review.
   */
  async updateReview(reviewId, updateData) {
    return apiClient(`/api/v1/reviews/${encodeURIComponent(reviewId)}/`, {
      method: 'PATCH',
      body: updateData,
    });
  },

  /**
   * Delete review.
   */
  async deleteReview(reviewId) {
    return apiClient(`/api/v1/reviews/${encodeURIComponent(reviewId)}/`, {
      method: 'DELETE',
    });
  },

  /**
   * List reviews for a specific media item.
   */
  async getMediaReviews(mediaId) {
    return apiClient('/api/v1/reviews/', {
      method: 'GET',
      params: { media: mediaId },
    });
  },
};
