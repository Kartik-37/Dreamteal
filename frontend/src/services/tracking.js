/**
 * DreamTeal Tracking & Diary Service
 */

import { apiClient } from './api';

export const trackingService = {
  /**
   * Fetch user tracking statuses.
   * @param {object} params - { media, media_id }
   */
  async getStatuses(params = {}) {
    return apiClient('/api/v1/tracking/status/', {
      method: 'GET',
      params,
    });
  },

  /**
   * Fetch tracking status for a specific media item.
   */
  async getStatusForMedia(mediaId) {
    const list = await apiClient('/api/v1/tracking/status/', {
      method: 'GET',
      params: { media: mediaId },
    });
    if (Array.isArray(list) && list.length > 0) {
      return list[0];
    }
    if (list && Array.isArray(list.results) && list.results.length > 0) {
      return list.results[0];
    }
    return null;
  },

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
   * Delete tracking status.
   */
  async deleteStatus(statusId) {
    return apiClient(`/api/v1/tracking/status/${encodeURIComponent(statusId)}/`, {
      method: 'DELETE',
    });
  },

  /**
   * Fetch user media progress records.
   * @param {object} params - { media, media_id }
   */
  async getProgress(params = {}) {
    return apiClient('/api/v1/tracking/progress/', {
      method: 'GET',
      params,
    });
  },

  /**
   * Fetch progress record for a specific media item.
   */
  async getProgressForMedia(mediaId) {
    const list = await apiClient('/api/v1/tracking/progress/', {
      method: 'GET',
      params: { media: mediaId },
    });
    if (Array.isArray(list) && list.length > 0) {
      return list[0];
    }
    if (list && Array.isArray(list.results) && list.results.length > 0) {
      return list.results[0];
    }
    return null;
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
