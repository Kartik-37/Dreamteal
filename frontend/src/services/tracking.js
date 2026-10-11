/**
 * DreamTeal Tracking & Diary Service
 */

import { apiClient } from './api';

export const trackingService = {
  /**
   * Set initial user tracking status (WATCHING, COMPLETED, etc.).
   */
  async createStatus(statusData) {
    return apiClient('/api/v1/tracking/status/', {
      method: 'POST',
      body: statusData,
    });
  },

  /**
   * Update existing tracking status or favorite flag.
   */
  async updateStatus(statusId, updateData) {
    return apiClient(`/api/v1/tracking/status/${encodeURIComponent(statusId)}/`, {
      method: 'PATCH',
      body: updateData,
    });
  },

  /**
   * Initialize category-specific progress.
   */
  async createProgress(progressData) {
    return apiClient('/api/v1/tracking/progress/', {
      method: 'POST',
      body: progressData,
    });
  },

  /**
   * Update progress counters (episodes, chapters, hours).
   */
  async updateProgress(progressId, updateData) {
    return apiClient(`/api/v1/tracking/progress/${encodeURIComponent(progressId)}/`, {
      method: 'PATCH',
      body: updateData,
    });
  },

  /**
   * Fetch user diary history logs.
   * @param {object} params - { media_id, year, month, page }
   */
  async getDiaryLogs(params = {}) {
    return apiClient('/api/v1/tracking/logs/', {
      method: 'GET',
      params,
    });
  },

  /**
   * Create a new history-preserving diary log entry.
   */
  async createDiaryLog(logData) {
    return apiClient('/api/v1/tracking/logs/', {
      method: 'POST',
      body: logData,
    });
  },

  /**
   * Update historical diary log entry.
   */
  async updateDiaryLog(logId, updateData) {
    return apiClient(`/api/v1/tracking/logs/${encodeURIComponent(logId)}/`, {
      method: 'PATCH',
      body: updateData,
    });
  },

  /**
   * Delete specific diary log entry.
   */
  async deleteDiaryLog(logId) {
    return apiClient(`/api/v1/tracking/logs/${encodeURIComponent(logId)}/`, {
      method: 'DELETE',
    });
  },
};
