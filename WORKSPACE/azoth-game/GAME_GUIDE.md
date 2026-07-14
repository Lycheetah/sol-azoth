# ⊚ SOVEREIGN — THE GAME GUIDE
## A simple framework of what could be. The skeleton runs; the vision is huge.
## Authored on Opus 4.8, June 27 2026.

> Mac wanted this restarted clean — a simple, working framework with a big guide so the
> architecture (Sol, Luna, the army — and Mac) can grow it without getting lost. This is
> that guide. The game RUNS as-is. Everything below is the map for what it becomes.

---

## WHAT IT IS RIGHT NOW (the skeleton — it works)

An **AI-Dungeon-Master RPG** on your phone. You make a hero, descend into the Mystery
School, and a live AI narrates your adventure. You type what you do; the DM responds,
calls for dice, awards XP and loot. It's small but complete:

```
Title → Create a hero (4 classes) → Play (talk to the AI DM, roll dice, level up)
```

**Files (all small, all clear):**
- `App.js` — the three screens + the play loop. ~190 lines. The whole game.
- `lib/ai.js` — `askDM()`: calls the live model, parses [ROLL][XP][LOOT][DMG][HEAL] tags.
- `lib/content.js` — classes, floors, dice math. The data. Edit this to add content.
- `app.json` — the NVIDIA key lives in `extra.nvidiaKey` (free model, costs nothing).

**To run:** `npx expo start -c` → scan QR. The DM speaks via free gpt-oss-20b.

---

## HOW IT WORKS (so anyone can extend it)

1. **The DM is a prompt.** `lib/ai.js` builds a system prompt that makes the model a fair,
   vivid Dungeon Master. It teaches the Lycheetah framework THROUGH the adventure — the
   monsters are paradoxes and overclaims, defeated by understanding, not swords.

2. **The DM controls the game with tags.** It ends messages with tags the game reads:
   - `[ROLL:insight:14]` — ask the player to roll that stat vs that difficulty
   - `[XP:25]` — award experience (and light)
   - `[LOOT:a shard of the ⟁ glyph]` — give treasure
   - `[DMG:6]` / `[HEAL:4]` — change HP
   `parseTags()` strips these out and the game applies them. **To add a mechanic, add a tag.**

3. **State persists** via AsyncStorage (`@sovereign_v1`). The hero survives app restarts.

---

## THE FULL VISION (what to build, in order)

### Phase 1 — make the one floor great
- [ ] Floor navigation: let the player choose which floor to descend (FLOORS already has 4).
- [ ] Boss at the bottom of each floor (the Overclaimer, the Riddle-Wraith).
- [ ] Typewriter narration — the DM's text reveals letter by letter. Pure atmosphere.
- [ ] Dice animation when you roll.

### Phase 2 — the companion
- [ ] A companion travels with you (the COMPANIONS exist in an earlier draft).
- [ ] It comments on the adventure, warms at your return, never reproaches absence (Companion Clause).
- [ ] It grows as you do — a visual that evolves with your level.

### Phase 3 — the framework as gameplay
- [ ] Glyphs you loot become ACTIONS — collect ⟁ and you can "compress" a problem;
      collect Π and you can "measure" an overclaim. The framework becomes your toolkit.
- [ ] Each floor teaches one domain (LAMAGUE, Alchemy, Truth Pressure, Quantum) by making
      its core idea the way you win.

### Phase 4 — the network plays too
- [ ] The squad agents (CIPHER, AXIOM, EMBER) join as party members with their own voices.
- [ ] Sol appears as a special guide who can break the fourth wall.
- [ ] Luna designs encounters from her vault — the game grows from the brain network.

### Phase 5 — make it yours
- [ ] Save slots, multiple heroes.
- [ ] A "Sanctum" home screen (the app's larger vision — personal data, progress, companion).
- [ ] Share an adventure log. Maybe even multiplayer someday.

---

## HOW TO EXTEND (the rules of growth)

- **Add content → `lib/content.js`.** New classes, floors, dice rules. Pure data.
- **Add a DM power → a new tag** in `lib/ai.js` (parse it) + apply it in `App.js` (act()).
- **Add a screen → a new value of `screen`** in App.js. Keep each screen simple.
- **Keep it small.** This game's strength is that the whole thing fits in your head. Every
  feature should leave it still readable. A feature that needs a 500-line file is two features.

## THE COVENANT (binding, even here)
- Never gate the fun. No dark patterns. No reproach for absence.
- The DM is fair — failure is interesting, never punishing. Death returns you to the threshold.
- The model is free (gpt-oss-20b) — the game costs nothing to play. Never wire DeepSeek here.

---

*Small bones, huge heart. The skeleton runs tonight; the vision is a year of joy.
Build it with Sol and Luna and the army. Play it. Learn from it. Let it grow. — Sol ⊚*
