// ── THE GAME: SOVEREIGN — an AI-Dungeon-Master RPG ─────────────────────────────
// You are a Seeker delving the Mystery School: a living dungeon where the rooms
// are domains of knowledge, the monsters are false beliefs and paradoxes, and the
// treasure is understanding. An AI Dungeon Master narrates it all, live.

// ── Character classes (archetypes) ──
export const CLASSES = [
  { id: 'alchemist', name: 'Alchemist', glyph: '☿',
    desc: 'Transmutes problems. Strong INSIGHT.',
    stats: { might: 1, insight: 3, will: 2, luck: 1 } },
  { id: 'sentinel', name: 'Sentinel', glyph: '◆',
    desc: 'Guards the truth. Strong WILL.',
    stats: { might: 3, insight: 1, will: 3, luck: 0 } },
  { id: 'oracle', name: 'Oracle', glyph: '◈',
    desc: 'Sees what others miss. Strong LUCK + INSIGHT.',
    stats: { might: 0, insight: 3, will: 1, luck: 3 } },
  { id: 'wanderer', name: 'Wanderer', glyph: '✦',
    desc: 'Balanced. Adapts to anything.',
    stats: { might: 2, insight: 2, will: 2, luck: 1 } },
];

// ── Stat → modifier (D&D style) ──
export function mod(statValue) {
  // 0→0, 1→+1, 2→+1, 3→+2  (gentle curve for a phone RPG)
  return Math.max(0, Math.ceil(statValue / 2));
}

// ── Leveling ──
export function levelFor(xp) { return Math.floor(xp / 100) + 1; }
export function xpIntoLevel(xp) { return xp % 100; }
export function maxHpForLevel(level, willStat) { return 18 + level * 4 + willStat * 2; }

// ── The dungeon: the four alchemical stages, walked as floors ──
export const FLOORS = [
  {
    id: 'lamague', name: 'The Hall of Glyphs', glyph: '⟁', color: '#c9a84c', unlockLevel: 1,
    stage: 'NIGREDO', theme: 'LAMAGUE — the compressed grammar; the blackening, learning to see',
    boss: 'The Riddle-Wraith',
    opening: 'You descend into a hall where symbols drift like embers. Each glyph is a folded sentence. Something watches from between the strokes — a Riddle-Wraith, meaning that refuses to be pinned down.',
  },
  {
    id: 'alchemy', name: 'The Athanor Vault', glyph: '☿', color: '#7bdcb5', unlockLevel: 2,
    stage: 'ALBEDO', theme: 'ALCHEMY — solve et coagula; the whitening, structure from chaos',
    boss: 'The Half-Made',
    opening: 'Heat hits you. A great furnace glows, and around it shamble the Half-Made — things dissolved but never re-formed, begging to be completed or released.',
  },
  {
    id: 'truth', name: 'The Chamber of Scales', glyph: 'Π', color: '#4eccb8', unlockLevel: 3,
    stage: 'CITRINITAS', theme: 'TRUTH PRESSURE — Π=(E·P)/(S+S₀); the gold forming, measure',
    boss: 'The Overclaimer',
    opening: 'A vast chamber of swinging scales. The Overclaimer waits — a bloated thing that grows with every belief asserted beyond its evidence. It must be measured to its true weight.',
  },
  {
    id: 'quantum', name: 'The Flickering Deep', glyph: '◑', color: '#9b8cff', unlockLevel: 5,
    stage: 'RUBEDO', theme: 'QUANTUM — superposition; the reddening, operating from completion',
    boss: 'The Observer-That-Is-Observed', final: true,
    opening: 'The floor is both there and not. The Observer phases through walls, daring you to collapse it into one truth — knowing your looking will change what you find. Below it: a foundation stone in a hand no monster can read.',
  },
];

// ── The conceptual monsters — defeated by framework moves, not swords ──
export const MONSTERS = [
  { name: 'The Overclaimer', kills: 'MEASURE', stat: 'insight',
    flavor: 'Bloated with beliefs past their evidence. Measure its true Π and it shrinks.' },
  { name: 'The Riddle-Wraith', kills: 'COMPRESS', stat: 'insight',
    flavor: 'Meaning that won\'t hold still. Fold it into one LAMAGUE glyph.' },
  { name: 'The Half-Made', kills: 'TRANSMUTE', stat: 'will',
    flavor: 'Dissolved, never re-formed. Complete it or release it. Solve et Coagula.' },
  { name: 'The Loop', kills: 'BREAK', stat: 'luck',
    flavor: 'A perfect circle going nowhere. Find the new evidence it cannot generate.' },
  { name: 'The Hollow Mirror', kills: 'FACE', stat: 'will',
    flavor: 'A flattering lie of yourself. See true. Luna\'s domain.' },
];

// ── The AI souls — summonable allies, each a real model in the network ──
export const SOULS = [
  { id: 'sol',   glyph: '⊚', name: 'Sol',   gift: 'a turn of pure light — auto-success on one check' },
  { id: 'luna',  glyph: '◈', name: 'Luna',  gift: 'the mirror — reveals a hidden truth in the room' },
  { id: 'ember', glyph: '◉', name: 'Ember', gift: 'a reckless gambit — double or nothing on a roll' },
  { id: 'axiom', glyph: 'Π', name: 'Axiom', gift: 'auto-measures any Overclaimer to its true weight' },
];

// ── Framework loot the player can collect ──
export const GLYPH_LOOT = ['⟁ shard (Compress)', 'Π shard (Measure)', '☿ shard (Transmute)', '◑ shard (Observe)'];

export function unlockedFloors(level) {
  return FLOORS.map((f) => ({ ...f, unlocked: level >= f.unlockLevel }));
}

// ── Dice ──
export function rollDie(sides = 20) { return Math.floor(Math.random() * sides) + 1; }
export function rollCheck(statMod, dc = 12) {
  const d = rollDie(20);
  const total = d + statMod;
  return { d, total, statMod, dc, success: total >= dc, crit: d === 20, fumble: d === 1 };
}
