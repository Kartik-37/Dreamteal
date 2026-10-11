import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Menu, X, LogIn, LogOut, User, Compass, BookOpen, Bookmark, Sparkles } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useAuth } from '../../hooks/useAuth';
import { AuthModal } from '../forms/AuthModal';
import { Button } from '../ui/Button';

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);

  const navLinks = [
    { name: 'Explore', path: '/', icon: Compass },
    { name: 'Diary', path: '/diary', icon: BookOpen },
    { name: 'Collections', path: '/collections', icon: Bookmark },
    { name: 'Recommendations', path: '/recommendations', icon: Sparkles },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 w-full bg-background-deep/90 backdrop-blur-md border-b border-border-neutral">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Brand Logo */}
          <Link
            to="/"
            className="flex items-center gap-2.5 focus-ring rounded-lg py-1 px-1.5"
            aria-label="DreamTeal Home"
          >
            <div className="w-8 h-8 rounded-lg bg-surface-2 border border-border-neutral flex items-center justify-center shadow-sm">
              <span className="w-3.5 h-3.5 rounded-full bg-teal shadow-glow inline-block" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight text-text-primary">
                Dream<span className="text-teal">Teal</span>
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav
            className="hidden md:flex items-center gap-1"
            aria-label="Main Navigation"
          >
            {navLinks.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.path}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors focus-ring',
                      isActive
                        ? 'text-teal bg-surface-2 border border-border-neutral'
                        : 'text-text-secondary hover:text-text-primary hover:bg-surface-1'
                    )
                  }
                >
                  <Icon className="w-4 h-4 opacity-80" aria-hidden="true" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* User Auth Action (Desktop) */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-2 border border-border-neutral text-xs">
                  <User className="w-3.5 h-3.5 text-teal" />
                  <span className="font-medium text-text-primary">
                    {user?.display_name || user?.username}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  icon={LogOut}
                  title="Sign Out"
                >
                  Sign Out
                </Button>
              </div>
            ) : (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setAuthModalOpen(true)}
                icon={LogIn}
              >
                Sign In
              </Button>
            )}
          </div>

          {/* Mobile Menu Hamburger Toggle */}
          <div className="flex md:hidden items-center gap-2">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileMenuOpen}
              className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-2 focus-ring"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border-neutral bg-surface-1 px-4 pt-3 pb-6 space-y-3">
            <nav className="flex flex-col gap-1">
              {navLinks.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.name}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors',
                        isActive
                          ? 'text-teal bg-surface-2 border border-border-neutral'
                          : 'text-text-secondary hover:text-text-primary hover:bg-surface-2'
                      )
                    }
                  >
                    <Icon className="w-4 h-4 opacity-80" />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </nav>

            <div className="pt-3 border-t border-border-neutral/60">
              {isAuthenticated ? (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-text-primary">
                    <User className="w-4 h-4 text-teal" />
                    <span>{user?.display_name || user?.username}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      logout();
                      setMobileMenuOpen(false);
                    }}
                    icon={LogOut}
                  >
                    Sign Out
                  </Button>
                </div>
              ) : (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setAuthModalOpen(true);
                    setMobileMenuOpen(false);
                  }}
                  icon={LogIn}
                  className="w-full"
                >
                  Sign In
                </Button>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Session Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />
    </>
  );
}
