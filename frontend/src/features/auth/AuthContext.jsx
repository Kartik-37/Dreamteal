import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../../services/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Initialize session and prefetch CSRF on startup
  const initAuth = useCallback(async () => {
    try {
      setLoading(true);
      setAuthError(null);
      // Ensure CSRF cookie is initialized from backend
      await authService.getCsrf();
      // Check active Django session
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      // Unauthenticated session is normal for guest visitors
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  const login = async (username, password) => {
    setLoading(true);
    setAuthError(null);
    try {
      const response = await authService.login(username, password);
      if (response && response.user) {
        setUser(response.user);
        return { success: true, user: response.user };
      }
      return { success: true };
    } catch (err) {
      const msg = err.message || 'Login failed. Please check your credentials.';
      setAuthError(msg);
      return { success: false, error: msg };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
    } catch (err) {
      console.warn('Logout error:', err.message);
    } finally {
      setUser(null);
      setAuthError(null);
      setLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
      return currentUser;
    } catch (err) {
      setUser(null);
      return null;
    }
  };

  const value = {
    user,
    isAuthenticated: Boolean(user),
    loading,
    authError,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
