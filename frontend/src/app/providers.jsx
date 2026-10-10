import React from 'react';
import { AuthProvider } from '../features/auth/AuthContext';

/**
 * Global application providers wrapper.
 */
export function AppProviders({ children }) {
  return <AuthProvider>{children}</AuthProvider>;
}
