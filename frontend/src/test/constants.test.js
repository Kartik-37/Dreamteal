import { test, expect, describe } from 'vitest';
import {
  REACTIONS,
  REACTION_LIST,
  MEDIA_CATEGORIES,
  TRACKING_STATUSES,
} from '../utils/constants.js';

describe('Reaction Taxonomy & Design System Tokens', () => {
  test('matches approved Phase 0 decisions exactly', () => {
    const keys = REACTION_LIST.map((r) => r.key);
    expect(keys).toEqual(['peak', 'loved_it', 'good_time', 'not_my_thing', 'skip']);

    expect(REACTIONS.PEAK.label).toBe('Peak');
    expect(REACTIONS.LOVED_IT.label).toBe('Loved It');
    expect(REACTIONS.GOOD_TIME.label).toBe('Good Time');
    expect(REACTIONS.NOT_MY_THING.label).toBe('Not My Thing');
    expect(REACTIONS.SKIP.label).toBe('Skip');

    // Verify approved color tokens
    expect(REACTIONS.PEAK.colorToken).toBe('electric-gold');
    expect(REACTIONS.LOVED_IT.colorToken).toBe('warm-coral');
    expect(REACTIONS.GOOD_TIME.colorToken).toBe('radiant-teal');
    expect(REACTIONS.NOT_MY_THING.colorToken).toBe('muted-lavender');
    expect(REACTIONS.SKIP.colorToken).toBe('crimson');

    // Strict zero-star policy verification: No stars, numeric values, or scores
    for (const reaction of REACTION_LIST) {
      expect(typeof reaction.label).toBe('string');
      expect(reaction.label).not.toContain('★');
      expect(reaction.label).not.toContain('☆');
      expect(reaction.label).not.toContain('⭐');
      expect('stars' in reaction).toBe(false);
      expect('numeric_value' in reaction).toBe(false);
      expect('score' in reaction).toBe(false);
    }
  });

  test('covers all 5 approved entertainment media categories', () => {
    const catKeys = Object.keys(MEDIA_CATEGORIES);
    expect(catKeys).toEqual(['MOVIE', 'SERIES', 'MANGA', 'MANHWA', 'GAME']);
  });

  test('covers all approved user tracking statuses', () => {
    const statusKeys = Object.keys(TRACKING_STATUSES);
    expect(statusKeys).toEqual(['WATCHING', 'COMPLETED', 'PLAN_TO_WATCH', 'ON_HOLD', 'DROPPED']);
  });
});
