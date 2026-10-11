/**
 * DreamTeal Global Constants & Taxonomy Definitions
 * Strictly Non-Numeric: Zero stars, zero numeric ratings.
 */

export const REACTIONS = {
  PEAK: {
    key: 'peak',
    label: 'Peak',
    color: '#f59e0b',
    colorToken: 'electric-gold',
    bg: 'rgba(245, 158, 11, 0.12)',
    border: 'rgba(245, 158, 11, 0.35)',
    description: 'An exceptional experience that the user strongly recommends.',
    badgeClass: 'text-[#f59e0b] bg-[rgba(245,158,11,0.12)] border-[rgba(245,158,11,0.35)]',
  },
  LOVED_IT: {
    key: 'loved_it',
    label: 'Loved It',
    color: '#fb7185',
    colorToken: 'warm-coral',
    bg: 'rgba(251, 113, 133, 0.12)',
    border: 'rgba(251, 113, 133, 0.35)',
    description: 'A genuinely enjoyable experience that the user highly values.',
    badgeClass: 'text-[#fb7185] bg-[rgba(251,113,133,0.12)] border-[rgba(251,113,133,0.35)]',
  },
  GOOD_TIME: {
    key: 'good_time',
    label: 'Good Time',
    color: '#14b8a6',
    colorToken: 'radiant-teal',
    bg: 'rgba(20, 184, 166, 0.12)',
    border: 'rgba(20, 184, 166, 0.35)',
    description: 'Enjoyable and worth experiencing, but not exceptional.',
    badgeClass: 'text-[#14b8a6] bg-[rgba(20,184,166,0.12)] border-[rgba(20,184,166,0.35)]',
  },
  NOT_MY_THING: {
    key: 'not_my_thing',
    label: 'Not My Thing',
    color: '#a78bfa',
    colorToken: 'muted-lavender',
    bg: 'rgba(167, 139, 250, 0.12)',
    border: 'rgba(167, 139, 250, 0.35)',
    description: 'The user did not connect with it, even if the media may have strengths.',
    badgeClass: 'text-[#a78bfa] bg-[rgba(167,139,250,0.12)] border-[rgba(167,139,250,0.35)]',
  },
  SKIP: {
    key: 'skip',
    label: 'Skip',
    color: '#e11d48',
    colorToken: 'crimson',
    bg: 'rgba(225, 29, 72, 0.12)',
    border: 'rgba(225, 29, 72, 0.35)',
    description: 'The user would not recommend spending time on it.',
    badgeClass: 'text-[#e11d48] bg-[rgba(225,29,72,0.12)] border-[rgba(225,29,72,0.35)]',
  },
};

export const REACTION_LIST = [
  REACTIONS.PEAK,
  REACTIONS.LOVED_IT,
  REACTIONS.GOOD_TIME,
  REACTIONS.NOT_MY_THING,
  REACTIONS.SKIP,
];

export const MEDIA_CATEGORIES = {
  MOVIE: {
    key: 'MOVIE',
    label: 'Movie',
    aspect: 'aspect-poster',
    badgeClass: 'bg-indigo-950/40 text-indigo-300 border-indigo-800/40',
  },
  SERIES: {
    key: 'SERIES',
    label: 'TV Series',
    aspect: 'aspect-poster',
    badgeClass: 'bg-cyan-950/40 text-cyan-300 border-cyan-800/40',
  },
  MANGA: {
    key: 'MANGA',
    label: 'Manga',
    aspect: 'aspect-poster',
    badgeClass: 'bg-emerald-950/40 text-emerald-300 border-emerald-800/40',
  },
  MANHWA: {
    key: 'MANHWA',
    label: 'Manhwa',
    aspect: 'aspect-poster',
    badgeClass: 'bg-violet-950/40 text-violet-300 border-violet-800/40',
  },
  GAME: {
    key: 'GAME',
    label: 'Game',
    aspect: 'aspect-game',
    badgeClass: 'bg-amber-950/40 text-amber-300 border-amber-800/40',
  },
};

export const TRACKING_STATUSES = {
  WATCHING: {
    key: 'WATCHING',
    label: 'In Progress',
    color: '#38bdf8',
    badgeClass: 'text-sky-400 bg-sky-950/40 border-sky-800/50',
  },
  COMPLETED: {
    key: 'COMPLETED',
    label: 'Completed',
    color: '#34d399',
    badgeClass: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50',
  },
  PLAN_TO_WATCH: {
    key: 'PLAN_TO_WATCH',
    label: 'Plan to Experience',
    color: '#818cf8',
    badgeClass: 'text-indigo-400 bg-indigo-950/40 border-indigo-800/50',
  },
  ON_HOLD: {
    key: 'ON_HOLD',
    label: 'On Hold',
    color: '#fbbf24',
    badgeClass: 'text-amber-400 bg-amber-950/40 border-amber-800/50',
  },
  DROPPED: {
    key: 'DROPPED',
    label: 'Dropped',
    color: '#94a3b8',
    badgeClass: 'text-slate-400 bg-slate-800/40 border-slate-700/50',
  },
};
