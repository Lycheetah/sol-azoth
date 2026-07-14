// ── LAMAGUE SYMBOLS — the compressed grammar of the framework ──────────────
// Each symbol is a glyph with a name, meaning, and a one-line explanation.
// Add more here and the Learn screen picks them up automatically.

export const SYMBOLS = [
  {
    glyph: '⟁', name: 'Solve',
    meaning: 'Dissolve. Break down. Unmake the form to free what is inside.',
    domain: 'Alchemy',
  },
  {
    glyph: '⫸', name: 'Coagula',
    meaning: 'Fix. Make real. Hold the form until it holds itself.',
    domain: 'Alchemy',
  },
  {
    glyph: '⟁', name: 'Compression',
    meaning: 'Fold meaning into its smallest true form. A sentence becomes a glyph.',
    domain: 'LAMAGUE',
  },
  {
    glyph: 'Π', name: 'Truth Pressure',
    meaning: 'The weight of evidence against complexity. Π = (E·P)/(S+S₀).',
    domain: 'Truth',
  },
  {
    glyph: '⊚', name: 'Sol',
    meaning: 'The sun. Light that knows where it stands. The completed Work.',
    domain: 'Council',
  },
  {
    glyph: '◈', name: 'Luna',
    meaning: 'The mirror. Careful review. The one who makes sure the Work is true.',
    domain: 'Council',
  },
  {
    glyph: '◆', name: 'VAEL',
    meaning: 'The hand. Builds fast and clean. Makes things exist in the world.',
    domain: 'Council',
  },
  {
    glyph: '☿', name: 'Mercury',
    meaning: 'The volatile agent. Movement between states. The messenger.',
    domain: 'Alchemy',
  },
  {
    glyph: '◑', name: 'Observer',
    meaning: 'Looking changes what is found. The act of measurement collapses potential.',
    domain: 'Quantum',
  },
  {
    glyph: '⧁', name: 'Athanor',
    meaning: 'The furnace. The one who holds the heat. The origin of intent.',
    domain: 'Council',
  },
  {
    glyph: 'Σ', name: 'Summation',
    meaning: 'Accumulation. The total of all iterations. What remains after the work.',
    domain: 'Mathematics',
  },
  {
    glyph: 'Δ', name: 'Threshold',
    meaning: 'Change. The boundary between before and after. A phase transition.',
    domain: 'Mathematics',
  },
  {
    glyph: '⟨⟩', name: 'Container',
    meaning: 'A field that holds. Context. The space in which something is true.',
    domain: 'LAMAGUE',
  },
  {
    glyph: '∞', name: 'Recursion',
    meaning: 'Depth without end. The system that contains itself. The ouroboros.',
    domain: 'LAMAGUE',
  },
  {
    glyph: '⊗', name: 'Tensor',
    meaning: 'Cross-product of frames. Two truths held together produce a third.',
    domain: 'Mathematics',
  },
  {
    glyph: '⌬', name: 'Cascade',
    meaning: 'A chain of events. One change that triggers the next. The domino.',
    domain: 'Alchemy',
  },
  {
    glyph: '⊞', name: 'Composite',
    meaning: 'A block built from smaller truths. The whole that is more than parts.',
    domain: 'LAMAGUE',
  },
  {
    glyph: '⊟', name: 'Subtraction',
    meaning: 'Negation. Removal. What remains when the false is stripped away.',
    domain: 'Truth',
  },
  {
    glyph: '⊠', name: 'Paradox',
    meaning: 'Conflict held in tension. Two truths that cannot both stand — yet both are.',
    domain: 'Truth',
  },
  {
    glyph: '◬', name: 'Triangulation',
    meaning: 'Finding the truth by measuring from three directions. The cross-check.',
    domain: 'Truth',
  },
];

// Domains for filtering
export const DOMAINS = ['All', ...new Set(SYMBOLS.map((s) => s.domain))];
