import { test, expect, describe } from 'vitest';
import React from 'react';
import { renderToString } from 'react-dom/server';

import { ReactionBadge } from '../components/reactions/ReactionBadge.jsx';
import { ReactionSelector } from '../components/reactions/ReactionSelector.jsx';
import { MediaCategoryLabel } from '../components/media/MediaCategoryLabel.jsx';
import { MediaStatusBadge } from '../components/status/MediaStatusBadge.jsx';
import { ProgressIndicator } from '../components/status/ProgressIndicator.jsx';
import { MediaPosterCard } from '../components/media/MediaPosterCard.jsx';
import { MediaSkeleton } from '../components/media/MediaSkeleton.jsx';
import { EmptyState } from '../components/feedback/EmptyState.jsx';
import { ErrorMessage } from '../components/feedback/ErrorMessage.jsx';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner.jsx';
import { Button } from '../components/ui/Button.jsx';
import { REACTION_LIST, MEDIA_CATEGORIES, TRACKING_STATUSES } from '../utils/constants.js';

describe('Component Library Presentation & Props Verification', () => {
  test('ReactionBadge renders all 5 approved reactions with text labels without stars', () => {
    for (const reaction of REACTION_LIST) {
      const html = renderToString(React.createElement(ReactionBadge, { reactionKey: reaction.key }));
      expect(html).toContain(reaction.label);
      expect(html).not.toContain('★');
      expect(html).not.toContain('☆');
      expect(html).not.toContain('⭐');
    }
  });

  test('ReactionSelector renders all 5 qualitative reactions without stars or emojis', () => {
    const html = renderToString(React.createElement(ReactionSelector, { value: 'peak' }));
    expect(html).toContain('Peak');
    expect(html).toContain('Loved It');
    expect(html).toContain('Good Time');
    expect(html).toContain('Not My Thing');
    expect(html).toContain('Skip');
    expect(html).not.toContain('★');
    expect(html).not.toContain('⭐');
  });

  test('MediaPosterCard renders poster image and reaction badge when provided', () => {
    const media = {
      title: 'The Batman',
      release_year: 2022,
      media_type: 'MOVIE',
      poster_url: 'https://example.com/batman.jpg',
      reaction_consensus: 'peak',
    };
    const html = renderToString(React.createElement(MediaPosterCard, { media }));
    expect(html).toContain('The Batman');
    expect(html).toContain('2022');
    expect(html).toContain('https://example.com/batman.jpg');
    expect(html).toContain('Peak');
    expect(html).not.toContain('★');
  });

  test('MediaPosterCard gracefully renders placeholder when poster_url is missing', () => {
    const media = {
      title: 'Unknown Movie',
      release_year: 2023,
      media_type: 'MOVIE',
      poster_url: null,
    };
    const html = renderToString(React.createElement(MediaPosterCard, { media }));
    expect(html).toContain('Unknown Movie');
    expect(html).toContain('No Poster');
  });

  test('MediaCategoryLabel renders correct category tags', () => {
    for (const catKey of Object.keys(MEDIA_CATEGORIES)) {
      const html = renderToString(React.createElement(MediaCategoryLabel, { category: catKey }));
      expect(html).toContain(MEDIA_CATEGORIES[catKey].label);
    }
  });

  test('MediaStatusBadge renders correct tracking statuses', () => {
    for (const statusKey of Object.keys(TRACKING_STATUSES)) {
      const html = renderToString(React.createElement(MediaStatusBadge, { status: statusKey }));
      expect(html).toContain(TRACKING_STATUSES[statusKey].label);
    }
  });

  test('ProgressIndicator renders category-specific indicators and progress bars', () => {
    const htmlSeries = renderToString(
      React.createElement(ProgressIndicator, { category: 'SERIES', current: 5, total: 10 })
    );
    expect(htmlSeries).toContain('Ep 5 of 10');
    expect(htmlSeries).toContain('50%');

    const htmlGame = renderToString(
      React.createElement(ProgressIndicator, { category: 'GAME', current: 34.5, label: '34.5 hrs • Main Story' })
    );
    expect(htmlGame).toContain('34.5 hrs • Main Story');
  });

  test('Feedback components render accurately', () => {
    const spinnerHtml = renderToString(React.createElement(LoadingSpinner, { label: 'Loading titles...' }));
    expect(spinnerHtml).toContain('Loading titles...');

    const emptyHtml = renderToString(
      React.createElement(EmptyState, { title: 'Nothing Found', description: 'Zero results matching filter.' })
    );
    expect(emptyHtml).toContain('Nothing Found');
    expect(emptyHtml).toContain('Zero results matching filter.');

    const errorHtml = renderToString(
      React.createElement(ErrorMessage, { title: 'Network Error', message: 'Failed to reach server' })
    );
    expect(errorHtml).toContain('Network Error');
    expect(errorHtml).toContain('Failed to reach server');

    const skeletonHtml = renderToString(React.createElement(MediaSkeleton));
    expect(skeletonHtml).toContain('animate-pulse');
  });

  test('Button primitive renders variants and loading states', () => {
    const primaryHtml = renderToString(React.createElement(Button, { variant: 'primary' }, 'Submit'));
    expect(primaryHtml).toContain('Submit');
    expect(primaryHtml).toContain('bg-teal');

    const loadingHtml = renderToString(React.createElement(Button, { loading: true }, 'Saving'));
    expect(loadingHtml).toContain('animate-spin');
  });
});
