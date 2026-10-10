import { test, expect, describe } from 'vitest';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';

import { Navbar } from '../components/navigation/Navbar.jsx';
import { Footer } from '../components/navigation/Footer.jsx';
import { FoundationDemoPage } from '../features/catalog/FoundationDemoPage.jsx';
import { AuthProvider } from '../features/auth/AuthContext.jsx';

describe('Application Shell & Navigation Verification', () => {
  test('Navbar renders brand logo, navigation links, and sign in entry', () => {
    const html = renderToString(
      <MemoryRouter>
        <AuthProvider>
          <Navbar />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(html).toContain('Dream');
    expect(html).toContain('Teal');
    expect(html).toContain('Explore');
    expect(html).toContain('Diary');
    expect(html).toContain('Collections');
    expect(html).toContain('Recommendations');
    expect(html).toContain('Sign In');
  });

  test('Footer renders qualitative philosophy and reaction taxonomy summary', () => {
    const html = renderToString(<Footer />);
    expect(html).toContain('Zero star ratings');
    expect(html).toContain('Universal Reactions');
    expect(html).toContain('Peak');
    expect(html).toContain('Loved It');
    expect(html).toContain('Good Time');
    expect(html).toContain('Not My Thing');
    expect(html).toContain('Skip');
    expect(html).toContain('TMDB, AniList, Jikan &amp; RAWG');
  });

  test('FoundationDemoPage renders hero headline, reaction preview, and media cards', () => {
    const html = renderToString(
      <MemoryRouter>
        <AuthProvider>
          <FoundationDemoPage />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(html).toContain('Cinematic media tracking, built for intentional viewing.');
    expect(html).toContain('Interactive Reaction System Preview:');
    expect(html).toContain('The Batman');
    expect(html).toContain('Severance');
    expect(html).toContain('Cyberpunk 2077');
  });
});
