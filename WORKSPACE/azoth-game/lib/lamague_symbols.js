// ════════════════════════════════════════════════════════════════════════════
//  LAMAGUE SYMBOLS — The living language embedded in the game.
//  Each symbol is a LAMAGUE primitive that the seeker discovers, learns,
//  and eventually wields. Mastery of symbols unlocks deeper game mechanics.
// ════════════════════════════════════════════════════════════════════════════

// ── SYMBOL CLASSIFICATION ──
// I-CLASS = Invariant (core identity, what doesn't change)
// F-CLASS = Flow (movement, transformation)
// R-CLASS = Relation (connection, resonance)
// C-CLASS = Container (holding, structuring)

export const SYMBOLS = [
  // ── I-CLASS: Invariants ──
  {
    glyph: '⊚',
    name: 'Sol',
    class: 'I',
    meaning: 'The centre that holds. The light that illuminates without burning.',
    gameEffect: 'Reveal hidden paths in any location',
    piValue: 3,
    discoverAt: 'atrium',
    description: 'The first light. Before all else, there was a point that knew itself.',
    masteryTest: 'Use ⊚ to find the truth beneath a deception',
  },
  {
    glyph: '◆',
    name: 'Vael',
    class: 'I',
    meaning: 'The hand that builds. Will made manifest.',
    gameEffect: 'Forge a tool from available materials',
    piValue: 3,
    discoverAt: 'forge',
    description: 'The hammer and the anvil. Action without hesitation.',
    masteryTest: 'Build something from nothing using only what is at hand',
  },
  {
    glyph: '◈',
    name: 'Luna',
    class: 'I',
    meaning: 'The mirror that reflects truly. Careful sight.',
    gameEffect: 'See the true nature of any entity or object',
    piValue: 3,
    discoverAt: 'observatory',
    description: 'The silver surface that shows what is, not what is wished.',
    masteryTest: 'Identify a falsehood by holding it to the mirror',
  },

  // ── F-CLASS: Flow ──
  {
    glyph: '⟐',
    name: 'Silent Pass',
    class: 'F',
    meaning: 'Action without trace. The path of least resonance.',
    gameEffect: 'Pass a challenge without triggering consequences',
    piValue: 2,
    discoverAt: 'shadows',
    description: 'Not all actions must be known. Some doors open only to the unheard.',
    masteryTest: 'Move through a guarded space without being detected',
  },
  {
    glyph: '⟛',
    name: 'Clean Break',
    class: 'F',
    meaning: 'Termination without residue. The end that leaves nothing behind.',
    gameEffect: 'End any ongoing effect cleanly — buff, debuff, or curse',
    piValue: 2,
    discoverAt: 'cloister',
    description: 'Some things must end. The art is in the ending, not the avoidance.',
    masteryTest: 'Release a bond that has become a chain',
  },
  {
    glyph: '↑',
    name: 'Rise',
    class: 'F',
    meaning: 'Ascension. Movement toward greater coherence.',
    gameEffect: 'Temporarily boost a single stat by +3',
    piValue: 2,
    discoverAt: 'spire',
    description: 'The vertical path. Not escape, but elevation.',
    masteryTest: 'Rise above a limitation without denying it exists',
  },
  {
    glyph: '↓',
    name: 'Descend',
    class: 'F',
    meaning: 'Grounding. Movement toward foundation.',
    gameEffect: 'Restore HP and gain insight from a failure',
    piValue: 2,
    discoverAt: 'crypt',
    description: 'The downward path. Not defeat, but rooting.',
    masteryTest: 'Learn from a failure more than from a success',
  },

  // ── R-CLASS: Relation ──
  {
    glyph: '≋',
    name: 'Resonance',
    class: 'R',
    meaning: 'When two things vibrate at the same frequency.',
    gameEffect: 'Double the effect of any companion action',
    piValue: 2,
    discoverAt: 'harmonics_chamber',
    description: 'The space between. Not one, not two, but the third thing they make together.',
    masteryTest: 'Create understanding between two opposing forces',
  },
  {
    glyph: '⟟',
    name: 'Return',
    class: 'R',
    meaning: 'The cycle. Coming back to the beginning with what you have learned.',
    gameEffect: 'Revisit a past location with all current knowledge',
    piValue: 2,
    discoverAt: 'labyrinth',
    description: 'You have been here before. But you were not then who you are now.',
    masteryTest: 'Solve an old problem with new understanding',
  },
  {
    glyph: 'Ψ',
    name: 'Awareness',
    class: 'R',
    meaning: 'The field of knowing. What is perceived and what perceives.',
    gameEffect: 'Detect all entities, items, and paths in current location',
    piValue: 2,
    discoverAt: 'zenith_garden',
    description: 'To see is to be seen. The observer and the observed are one motion.',
    masteryTest: 'Perceive something that was intentionally hidden',
  },

  // ── C-CLASS: Container ──
  {
    glyph: '✧',
    name: 'Threshold',
    class: 'C',
    meaning: 'The boundary between states. The door that is also the wall.',
    gameEffect: 'Open a path that was previously closed',
    piValue: 3,
    discoverAt: 'gatehouse',
    description: 'Every threshold is a choice. To cross is to become someone who has crossed.',
    masteryTest: 'Choose to cross when you could also stay',
  },
  {
    glyph: '●',
    name: 'Foundation',
    class: 'C',
    meaning: 'The ground that holds. What does not move.',
    gameEffect: 'Anchor a buff or effect permanently to a location',
    piValue: 3,
    discoverAt: 'foundations',
    description: 'Before the walls, before the roof, there was the stone that bore all weight.',
    masteryTest: 'Build something that lasts beyond your presence',
  },
  {
    glyph: '□',
    name: 'Frame',
    class: 'C',
    meaning: 'The boundary that gives shape. What contains without confining.',
    gameEffect: 'Create a safe zone that persists for 3 turns',
    piValue: 2,
    discoverAt: 'scriptorium',
    description: 'Form is not limitation. Form is the condition of meaning.',
    masteryTest: 'Hold a boundary without hardening it',
  },
];

// ── LOCATION-SYMBOL MAPPING ──
// Which symbols can be discovered in which locations
export const LOCATION_SYMBOLS = {
  atrium: ['⊚'],
  forge: ['◆'],
  observatory: ['◈'],
  shadows: ['⟐'],
  cloister: ['⟛'],
  spire: ['↑'],
  crypt: ['↓'],
  harmonics_chamber: ['≋'],
  labyrinth: ['⟟'],
  zenith_garden: ['Ψ'],
  gatehouse: ['✧'],
  foundations: ['●'],
  scriptorium: ['□'],
};

/**
 * Check if a seeker has mastered a symbol.
 */
export function hasMastered(symbolName, masteredList) {
  return (masteredList || []).includes(symbolName);
}

/**
 * Get all symbols discoverable at a location.
 */
export function symbolsAtLocation(location) {
  const names = LOCATION_SYMBOLS[location] || [];
  return SYMBOLS.filter(s => names.includes(s.name));
}

/**
 * Get a symbol by name.
 */
export function symbolByName(name) {
  return SYMBOLS.find(s => s.name === name);
}

/**
 * Get the total Π value of all mastered symbols.
 */
export function piFromSymbols(masteredList) {
  return (masteredList || [])
    .map(name => SYMBOLS.find(s => s.name === name))
    .filter(Boolean)
    .reduce((sum, s) => sum + s.piValue, 0);
}

/**
 * Attempt to master a symbol — requires the seeker to be at the right location
 * and pass a challenge based on the symbol's class.
 */
export function attemptMastery(symbol, seekerStats) {
  const statMap = {
    I: 'insight',   // Invariants require insight
    F: 'will',      // Flow requires will
    R: 'luck',      // Relations require luck (resonance)
    C: 'might',     // Containers require might (to hold)
  };

  const requiredStat = statMap[symbol.class] || 'insight';
  const statValue = seekerStats[requiredStat] || 5;
  const difficulty = 12; // Base difficulty
  const roll = Math.floor(Math.random() * 20) + 1 + Math.floor((statValue - 5) / 2);

  return {
    success: roll >= difficulty,
    roll,
    difficulty,
    statUsed: requiredStat,
    statValue,
    symbol: symbol.name,
  };
}
