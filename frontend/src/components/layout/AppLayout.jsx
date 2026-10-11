import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../navigation/Navbar';
import { Footer } from '../navigation/Footer';

/**
 * AppLayout — Persistent shell containing header navigation,
 * dynamic page outlet, and footer.
 */
export function AppLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-background-deep text-text-primary">
      <Navbar />
      <main className="flex-1 w-full flex flex-col">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
