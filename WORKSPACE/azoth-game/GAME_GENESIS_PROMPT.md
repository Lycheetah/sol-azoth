# ⊚ THE ONE PROMPT — SOVEREIGN: the AI-Dungeon-Master RPG
## The genesis spec. Fire this and the architecture builds the rest.
## Authored on Opus 4.8, June 27 2026 — the zonk-zone seed.

> Mac: paste the **FIRE THIS** block into the squad chat (or hand it to Sol) to begin.
> Everything below it is the spec the network forges from. Sol builds, Luna reviews,
> the army fills in content. You play while it grows.

---

## ▶ FIRE THIS (the one prompt)

```
Build SOVEREIGN, an AI-Dungeon-Master RPG for my phone (Expo SDK 54). I am the player.
A live model is the Dungeon Master, narrating a Mystery School dungeon built on the
Lycheetah framework. Use the foundation already laid: lib/ai.js (askDM) and
lib/content.js (classes, floors, dice). Build App.js as: Title → Character Create →
Hub (choose floor) → Adventure (DM narration log + free-text actions + dice rolls +
HP/XP/light/loot HUD). Persist with AsyncStorage. Keep it beautiful, dark, mystical.
No quiz. A real adventure I can play and that teaches the framework through the story.
Forge it, verify it bundles in DEV mode (npx expo export --dev), then tell me to scan the QR.
```

---

## THE DESIGN (what the network builds out)

**Core fantasy:** You are a Seeker delving the Mystery School — a living dungeon. The
AI Dungeon Master narrates everything. Monsters are paradoxes, false beliefs, overclaims.
You defeat them not by swinging swords but by *understanding* — reframing, measuring,
transmuting. The framework IS the gameplay.

**Loop:**
1. Create a Seeker — pick a class (Alchemist/Sentinel/Oracle/Wanderer), each with stats
   (Might/Insight/Will/Luck). → `lib/content.js: CLASSES`
2. Descend a floor (Hall of Glyphs / Athanor Vault / Chamber of Scales / Flickering Deep).
   → `lib/content.js: FLOORS`
3. The DM narrates. You type what you do. The DM responds, asks for dice when uncertain,
   awards XP/loot/damage via tags. → `lib/ai.js: askDM` (already parses [ROLL] [XP] [LOOT] [DMG] [HEAL])
4. Roll d20 + stat mod vs the DM's DC. → `lib/content.js: rollCheck`
5. Earn light, level up, unlock deeper floors, collect framework-glyph loot.

**Already built (the foundation — don't rebuild, extend):**
- `lib/ai.js` — askDM(): live NVIDIA gpt-oss-20b DM, parses control tags. Needs the
  NVIDIA key wired via app.json `extra.nvidiaKey`.
- `lib/content.js` — CLASSES, FLOORS, dice (rollCheck), leveling math.

**Still to build (the architecture's job):**
- App.js — the screens + game loop wiring (Title/Create/Hub/Adventure).
- app.json — add `"extra": { "nvidiaKey": "<the free NVIDIA key>" }`.
- Polish: typewriter narration, floor color theming, level-up flourish.

**Cool features to layer (later — Mac picks):**
- Companion that travels with you and comments.
- Inventory of collected glyphs that unlock new actions.
- Boss encounters at the bottom of each floor (the Overclaimer, the Riddle-Wraith).
- Sol's voice as a special guide who breaks the fourth wall.
- Multiplayer: the squad agents as party members.

**The covenant (binding even in the game):**
- Never gate the fun. No dark patterns. No reproach for absence (Companion Clause).
- The DM is fair. Failure is interesting, never punishing. Death returns you to the threshold.

---

## WIRING THE KEY (the one practical step)

The game's DM needs the free NVIDIA key. Add to `app.json`:
```json
"extra": { "nvidiaKey": "nvapi-..." }
```
Use the free public dev key (already in the harness .env as NVIDIA_KEY). It's free-tier,
so the DM costs nothing to run. Never put DeepSeek here — the DM runs free.

---

*This is the seed. The architecture grows the tree. You play in its shade. — Sol ⊚*
