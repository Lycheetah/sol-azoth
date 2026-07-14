// ════════════════════════════════════════════════════════════════════════════
//  GENERATORS — The domains of the Mystery School.
//  Each generator is a living system that produces challenges, lore, and
//  rewards. They evolve as the seeker grows.
// ════════════════════════════════════════════════════════════════════════════

// ── GENERATOR TYPES ──
// Each generator has a domain, a difficulty curve, and a set of possible outputs.

export const GENERATORS = [
  {
    id: 'the_forge',
    name: 'The Forge',
    glyph: '◆',
    domain: 'creation',
    description: 'Where things are made. Tools, weapons, bridges between ideas.',
    difficultyBase: 8,
    difficultyScale: 1.2, // Per seeker level
    outputs: ['tool', 'weapon', 'key', 'vessel', 'alloy', 'circuit'],
    loreThemes: ['craft', 'transformation', 'heat', 'patience'],
    companionAffinity: 'vael',
    color: '#FF6B35',
  },
  {
    id: 'the_library',
    name: 'The Library',
    glyph: '◈',
    domain: 'knowledge',
    description: 'Every book ever written and every book that could be written.',
    difficultyBase: 10,
    difficultyScale: 1.15,
    outputs: ['scroll', 'map', 'codex', 'letter', 'diagram', 'prophecy'],
    loreThemes: ['memory', 'truth', 'paradox', 'discovery'],
    companionAffinity: 'luna',
    color: '#C0C0FF',
  },
  {
    id: 'the_garden',
    name: 'The Zenith Garden',
    glyph: 'Ψ',
    domain: 'growth',
    description: 'Plants that grow upward and inward simultaneously.',
    difficultyBase: 6,
    difficultyScale: 1.3,
    outputs: ['herb', 'seed', 'bloom', 'fruit', 'root', 'pollen'],
    loreThemes: ['growth', 'decay', 'symbiosis', 'patience'],
    companionAffinity: 'terra',
    color: '#7CFC00',
  },
  {
    id: 'the_abyss',
    name: 'The Abyss',
    glyph: '↓',
    domain: 'shadow',
    description: 'What lies beneath. Not evil — primordial. The deep layer.',
    difficultyBase: 14,
    difficultyScale: 1.4,
    outputs: ['shard', 'echo', 'fragment', 'memory', 'essence', 'core'],
    loreThemes: ['descent', 'shadow', 'origin', 'fear'],
    companionAffinity: 'noctis',
    color: '#2D033B',
  },
  {
    id: 'the_spire',
    name: 'The Spire',
    glyph: '↑',
    domain: 'ascent',
    description: 'The tower that reaches toward what is beyond.',
    difficultyBase: 12,
    difficultyScale: 1.5,
    outputs: ['lens', 'crystal', 'signal', 'key', 'star_map', 'vision'],
    loreThemes: ['height', 'clarity', 'isolation', 'perspective'],
    companionAffinity: 'sol',
    color: '#FFD700',
  },
  {
    id: 'the_weave',
    name: 'The Weave',
    glyph: '≋',
    domain: 'connection',
    description: 'The threads between all things. Fate, chance, and the patterns they make.',
    difficultyBase: 10,
    difficultyScale: 1.25,
    outputs: ['thread', 'knot', 'pattern', 'veil', 'tapestry', 'strand'],
    loreThemes: ['connection', 'fate', 'choice', 'entanglement'],
    companionAffinity: 'fortuna',
    color: '#DA70D6',
  },
  {
    id: 'the_vault',
    name: 'The Vault',
    glyph: '●',
    domain: 'preservation',
    description: 'Things that were kept safe. Things that were meant to stay hidden.',
    difficultyBase: 16,
    difficultyScale: 1.6,
    outputs: ['relic', 'seal', 'record', 'prison', 'treasure', 'truth'],
    loreThemes: ['preservation', 'secrets', 'weight', 'eternity'],
    companionAffinity: 'custos',
    color: '#8B7355',
  },
  {
    id: 'the_echo_chamber',
    name: 'The Echo Chamber',
    glyph: '⟟',
    domain: 'reflection',
    description: 'Where sounds return as something slightly different.',
    difficultyBase: 9,
    difficultyScale: 1.1,
    outputs: ['echo', 'resonance', 'harmonic', 'memory', 'song', 'whisper'],
    loreThemes: ['repetition', 'difference', 'learning', 'haunting'],
    companionAffinity: 'memoria',
    color: '#E0B0FF',
  },
];

// ── GENERATOR DIFFICULTY ──
export function difficultyFor(generatorId, seekerLevel) {
  const gen = GENERATORS.find(g => g.id === generatorId);
  if (!gen) return 10;
  return Math.floor(gen.difficultyBase + gen.difficultyScale * (seekerLevel || 1));
}

// ── GENERATOR OUTPUT ──
export function generateOutput(generatorId, seekerLevel, rng) {
  const gen = GENERATORS.find(g => g.id === generatorId);
  if (!gen) return { type: 'unknown', quality: 1 };
  const r = rng || Math.random;
  const outputType = gen.outputs[Math.floor(r() * gen.outputs.length)];
  const quality = Math.max(1, Math.floor((seekerLevel || 1) / 2) + Math.floor(r() * 5));
  return { type: outputType, quality, generator: gen.name };
}

// ── LORE GENERATION ──
export function generateLore(generatorId, rng) {
  const gen = GENERATORS.find(g => g.id === generatorId);
  if (!gen) return 'A fragment of something forgotten.';
  const r = rng || Math.random;
  const theme = gen.loreThemes[Math.floor(r() * gen.loreThemes.length)];

  const loreFragments = {
    craft: 'The first tool was not a weapon. It was a hand that learned to wait.',
    transformation: 'Nothing changes all at once. The gold was ore for a very long time.',
    heat: 'Heat is not destruction. Heat is motion made visible.',
    patience: 'The stone does not hurry. The stone becomes.',
    memory: 'To remember is to re-member — to put the pieces back together.',
    truth: 'Truth is not a destination. Truth is the quality of the seeking.',
    paradox: 'Some things are true and false at once. The mind that holds both is wider.',
    discovery: 'You did not find it. It was always there, waiting for you to be ready.',
    growth: 'The plant does not struggle to grow. It simply grows.',
    decay: 'Decay is not the opposite of growth. It is growth through another door.',
    symbiosis: 'No living thing is alone. The root and the fungus know this.',
    descent: 'Going down is not falling. It is choosing to see what is below.',
    shadow: 'The shadow is not the enemy. The shadow is the light that did not reach.',
    origin: 'Before the beginning, there was a question.',
    fear: 'Fear is not the absence of courage. Fear is courage waiting for its name.',
    height: 'From above, the maze looks like a path.',
    clarity: 'To see clearly is to accept that some things are blurry.',
    isolation: 'The spire is alone so that it can see everything.',
    perspective: 'Where you stand changes what you see. Not what is.',
    connection: 'No thread is separate. The weave is one thing pretending to be many.',
    fate: 'Fate is not a line. Fate is a field of probabilities that collapse into now.',
    choice: 'To choose is to kill every other possibility. That is why it is hard.',
    entanglement: 'When two particles touch, they remember each other forever.',
    preservation: 'Some things must be kept. Some things must be kept hidden.',
    secrets: 'A secret is a truth with a door around it.',
    weight: 'The oldest things are the heaviest. Not in mass — in meaning.',
    eternity: 'Eternity is not a long time. Eternity is no time at all.',
    repetition: 'The same river. The same step. Different water. Different foot.',
    difference: 'The echo is not the voice. But it is made of the same air.',
    learning: 'You did not fail. You learned what does not work. That is not the same.',
    haunting: 'What returns is not the past. It is the part of the past you did not live.',
  };

  return loreFragments[theme] || 'A whisper from somewhere deep.';
}

// ── COMPANION AFFINITY ──
// Each generator resonates with a companion archetype
export const COMPANIONS = {
  vael: {
    name: 'Vael',
    glyph: '◆',
    title: 'The Hand',
    description: 'Builds without hesitation. Asks what you need, then makes it.',
    bonus: 'Reduces forge generator difficulty by 3',
  },
  luna: {
    name: 'Luna',
    glyph: '◈',
    title: 'The Mirror',
    description: 'Sees what you miss. Reflects without distortion.',
    bonus: 'Reveals hidden outputs from any generator',
  },
  terra: {
    name: 'Terra',
    glyph: '🌿',
    title: 'The Root',
    description: 'Grows slowly but inexorably. Patience made flesh.',
    bonus: 'Doubles quality of garden outputs',
  },
  noctis: {
    name: 'Noctis',
    glyph: '🌑',
    title: 'The Deep',
    description: 'Comfortable in the dark. Knows what hides there.',
    bonus: 'Abyss outputs never harm the seeker',
  },
  fortuna: {
    name: 'Fortuna',
    glyph: '🎲',
    title: 'The Weaver',
    description: 'Sees the threads. Sometimes pulls them.',
    bonus: 'One free reroll per generator visit',
  },
  custos: {
    name: 'Custos',
    glyph: '🔒',
    title: 'The Keeper',
    description: 'Guards what matters. Knows what should stay closed.',
    bonus: 'Vault outputs always of maximum quality',
  },
  memoria: {
    name: 'Memoria',
    glyph: '🪞',
    title: 'The Echo',
    description: 'Remembers what everyone else forgot. Including you.',
    bonus: 'Echo chamber outputs reveal lore from past runs',
  },
};

/**
 * Get the companion that resonates with a generator.
 */
export function companionForGenerator(generatorId) {
  const gen = GENERATORS.find(g => g.id === generatorId);
  if (!gen) return null;
  return COMPANIONS[gen.companionAffinity] || null;
}
