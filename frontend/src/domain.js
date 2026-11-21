export const RULES = Object.freeze({ roundCount: 7, previewSeconds: 3, answerSeconds: 25, maxScore: 700 });

export const TIERS = {
  common:     { label: 'Public',       points: 10, tone: '#a7b2a9', symbol: '⬜' },
  too_clever: { label: 'Known Trick',  points: 15, tone: '#e2b375', symbol: '🟨' },
  familiar:   { label: 'User Space',   points: 30, tone: '#6ac5ed', symbol: '🟦' },
  rare:       { label: 'Privileged',   points: 60, tone: '#b8a1f2', symbol: '🟪' },
  deep_cut:   { label: 'Kernel',       points: 85, tone: '#6fe3bd', symbol: '🟩' },
  featured:   { label: 'Root Key',     points: 100, tone: '#c4f876', symbol: '🔑' },
};

export function scoreBand(score) {
  if (score <= 150) return 'common';
  if (score <= 250) return 'familiar';
  if (score <= 350) return 'rare';
  if (score <= 449) return 'deep_cut';
  return 'featured';
}

export function countdown(ms) {
  const seconds = Math.max(0, Math.ceil(ms / 1000));
  return [Math.floor(seconds / 3600), Math.floor(seconds / 60) % 60, seconds % 60]
    .map(part => String(part).padStart(2, '0')).join(':');
}
