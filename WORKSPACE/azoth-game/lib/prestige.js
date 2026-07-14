// ════════════════════════════════════════════════════════════════════════════
//  PRESTIGE — The cycle of dissolution and rebirth.
//  When a seeker has learned all they can in one life, they dissolve and
//  return with fragments of their former insight — the Solve et Coagula loop.
// ════════════════════════════════════════════════════════════════════════════

// Prestige thresholds — each requires total Π accumulated
const PRESTIGE_THRESHOLDS = [
  { level: 1, piRequired: 100,  title: 'Awakened',      bonus: 'Start with +1 to all stats' },
  { level: 2, piRequired: 300,  title: 'Illuminated',   bonus: 'Unlock the Codex of Echoes' },
  { level: 3, piRequired: 600,  title: 'Transmuted',    bonus: 'Start with one mastered LAMAGUE symbol' },
  { level: 4, piRequired: 1000, title: 'Philosopher',   bonus: 'All stat gains +50%' },
  { level: 5, piRequired: 2000, title: 'Adept',         bonus: 'Unlock the Dream Forge' },
  { level: 6, piRequired: 3500, title: 'Magnus',        bonus: 'Start every run with a companion soul' },
  { level: 7, piRequired: 5500, title: 'Aurum',         bonus: 'Gold resonance — all Π gains doubled' },
  { level: 8, piRequired: 8000, title: 'Azoth',         bonus: 'The Stone — permanent 10% to all rolls' },
];

// What carries over through a prestige
const CARRIED_FRAGMENTS = {
  prestigeLevel: true,        // The level itself
  masteredSymbols: true,      // LAMAGUE symbols learned
  companionBonds: true,       // Companion relationship levels
  discoveredSecrets: true,    // Lore fragments found
  totalPiEver: true,          // For threshold checking
};

// What resets
const RESET_ON_PRESTIGE = {
  stats: true,                // Back to base (modified by prestige bonuses)
  inventory: true,            // Items lost
  currentPi: true,            // Π resets to 0 (totalPiEver preserved)
  location: true,             // Back to the Atrium
  questProgress: true,        // Quests reset
};

/**
 * Check if a seeker is eligible for prestige.
 */
export function canPrestige(state) {
  const currentLevel = state.prestigeLevel || 0;
  const nextThreshold = PRESTIGE_THRESHOLDS.find(t => t.level === currentLevel + 1);
  if (!nextThreshold) return { eligible: false, reason: 'You have reached the highest known prestige.' };
  const eligible = (state.totalPiEver || 0) >= nextThreshold.piRequired;
  return {
    eligible,
    nextLevel: currentLevel + 1,
    nextTitle: nextThreshold.title,
    nextBonus: nextThreshold.bonus,
    piNeeded: Math.max(0, nextThreshold.piRequired - (state.totalPiEver || 0)),
    piRequired: nextThreshold.piRequired,
  };
}

/**
 * Execute a prestige — dissolve and return with fragments.
 * Returns the new state after prestige.
 */
export function executePrestige(oldState) {
  const currentLevel = oldState.prestigeLevel || 0;
  const threshold = PRESTIGE_THRESHOLDS.find(t => t.level === currentLevel + 1);
  if (!threshold) return oldState; // Can't prestige further

  const newLevel = currentLevel + 1;

  // Calculate stat bonuses from prestige level
  const statBonus = newLevel; // +1 to all base stats per prestige level

  // New base stats
  const newStats = {
    might: 5 + statBonus,
    insight: 5 + statBonus,
    will: 5 + statBonus,
    luck: 5 + statBonus,
  };

  return {
    // Carried fragments
    prestigeLevel: newLevel,
    prestigeTitle: threshold.title,
    masteredSymbols: oldState.masteredSymbols || [],
    companionBonds: oldState.companionBonds || {},
    discoveredSecrets: oldState.discoveredSecrets || [],
    totalPiEver: oldState.totalPiEver || 0,

    // Reset values
    stats: newStats,
    inventory: [],
    currentPi: 0,
    location: 'atrium',
    questProgress: {},

    // New state flags
    prestigeBonus: threshold.bonus,
    prestigeHistory: [...(oldState.prestigeHistory || []), {
      level: newLevel,
      title: threshold.title,
      timestamp: Date.now(),
    }],
  };
}

/**
 * Get the title for a prestige level.
 */
export function titleForLevel(level) {
  const t = PRESTIGE_THRESHOLDS.find(p => p.level === level);
  return t ? t.title : 'Seeker';
}

/**
 * Get all prestige bonuses active for a given level.
 */
export function bonusesForLevel(level) {
  return PRESTIGE_THRESHOLDS
    .filter(t => t.level <= level)
    .map(t => ({ level: t.level, title: t.title, bonus: t.bonus }));
}

export { PRESTIGE_THRESHOLDS };
