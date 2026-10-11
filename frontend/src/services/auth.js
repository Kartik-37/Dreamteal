/**
 * DreamTeal Authentication Service
 * Communicates with Django session authentication endpoints.
 */

import { apiClient, ensureCsrfToken } from './api';

export const authService = {
  /**
   * Fetch and initialize CSRF token cookie.
   */
  async getCsrf() {
    return ensureCsrfToken();
  },

  /**
   * Authenticate with username and password.
   * Django establishes sessionid cookie.
   */
  async login(username, password) {
    return apiClient('/api/v1/users/login/', {
      method: 'POST',
      body: { username, password },
    });
  },

  /**
   * Log out active session.
   */
  async logout() {
    return apiClient('/api/v1/users/logout/', {
      method: 'POST',
    });
  },

  /**
   * Retrieve currently authenticated user profile.
   * Returns null if unauthenticated (401).
   */
  async getCurrentUser() {
    try {
      return await apiClient('/api/v1/users/me/', {
        method: 'GET',
      });
    } catch (err) {
      if (err.isAuthError) {
        return null;
      }
      throw err;
    }
  },

  /**
   * Update active user profile.
   */
  async updateProfile(profileData) {
    return apiClient('/api/v1/users/me/', {
      method: 'PATCH',
      body: profileData,
    });
  },
};
