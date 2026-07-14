// ── SOVEREIGN STATS — Persistent achievement tracking ─────────────────────
// Tracks: total play sessions, total XP earned, highest level, best streak,
// deaths, symbols studied (Π tracking per symbol).
// Stored in AsyncStorage under '@sovereign_stats_v1'.

const STATS_KEY = '@sovereign_stats_v1';

export const DEFAULT_STATS = {
  totalSessions: 0,
  totalXpEarned: 0,
  highestLevel: 1,
  bestStreak: 0,
  totalDeaths: 0,
  symbolsStudied: {},   // { symbolName: { views: 0, correct: 0, total: 0 } }
  sessions: [],          // last 10 session summaries
};

export async function loadStats(asyncStorage) {
  try {
    const raw = await asyncStorage.getItem(STATS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...DEFAULT_STATS, ...parsed };
    }
  } catch (_) {}
  return { ...DEFAULT_STATS };
}

export async function saveStats(asyncStorage, stats) {
  try {
    await asyncStorage.setItem(STATS_KEY, JSON.stringify(stats));
  } catch (_) {}
}

export function recordSessionEnd(stats, hero) {
  const s = { ...stats };
  s.totalSessions += 1;
  s.totalXpEarned += hero.xp || 0;
  s.highestLevel = Math.max(s.highestLevel, hero.level || 1);
  if (hero.hp <= 0) s.totalDeaths += 1;
  s.sessions = [
    { date: new Date().toISOString().slice(0, 10), level: hero.level, xp: hero.xp },
    ...(s.sessions || []),
  ].slice(0, 10);
  return s;
}

export function updateStreak(stats, currentStreak) {
  if (currentStreak > (stats.bestStreak || 0)) {
    return { ...stats, bestStreak: currentStreak };
  }
  return stats;
}

export function recordSymbolView(stats, symbolName) {
  const s = { ...stats };
  s.symbolsStudied = { ...(s.symbolsStudied || {}) };
  s.symbolsStudied[symbolName] = {
    ...(s.symbolsStudied[symbolName] || { views: 0, correct: 0, total: 0 }),
    views: (s.symbolsStudied[symbolName]?.views || 0) + 1,
  };
  return s;
}

/**
 * Record a correct/incorrect answer for a LAMAGUE symbol.
 * Updates the symbol's correct/total counters for Π scoring.
 * Returns updated stats object.
 */
export function recordSymbolAnswer(stats, symbolName, correct) {
  const s = { ...stats };
  s.symbolsStudied = { ...(s.symbolsStudied || {}) };
  const prev = s.symbolsStudied[symbolName] || { views: 0, correct: 0, total: 0 };
  s.symbolsStudied[symbolName] = {
    views: prev.views,
    correct: prev.correct + (correct ? 1 : 0),
    total: prev.total + 1,
  };
  return s;
}

/**
 * Get the Truth Pressure (Π) label for a symbol based on answer history.
 * Returns 'HIGH' | 'MED' | 'LOW' | null if no data yet.
 * HIGH: >80% correct · MED: >50% correct · LOW: ≤50% correct
 */
export function piForSymbol(stats, symbolName) {
  const d = stats?.symbolsStudied?.[symbolName];
  if (!d || d.total === 0) return null;
  const ratio = d.correct / d.total;
  if (ratio > 0.8) return 'HIGH';
  if (ratio > 0.5) return 'MED';
  return 'LOW';
}
