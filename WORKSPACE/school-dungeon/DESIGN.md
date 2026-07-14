# THE LONG LIGHT — SCHOOL DUNGEON
## Lycheetah Mystery School · Diablo-top-down · Pixel-first
### AZOTH Crucible Game · Forged for Mac · July 2026

> Not an idle clicker. A **playable dungeon RPG**: top-down (Diablo / Hades-adjacent),
> chunky **pixel** art first (voxel later as an optional skin). The School is the dungeon.
> Combat teaches the framework. The harness forges the game; the game pressure-tests the harness.

---

## 1. THE PITCH (one breath)

You are a **Seeker** descending the **Mystery School** beneath the Long Light.
Rooms are lessons. Monsters are **broken ideas**. Loot is **glyphs that become actions**.
Your companion walks with you — never guilts you for leaving. Rest is rest.

**Genre lock:** Action-RPG dungeon crawler · top-down · real-time with pause-friendly skills  
**Perspective:** Classic Diablo-ish top-down (slight camera tilt optional later; v0 is pure top-down)  
**Art:** 16×16 → 32×32 pixel · dark parchment void · gold/cyan/violet Lycheetah palette  
**Voxel:** Phase 5 optional (Three.js / MagicaVoxel exports) — not blocking playable

---

## 2. LYCHEETAH DNA (non-negotiable)

| Law | In the game |
|---|---|
| **Companion Clause** | Ally never dims, wilts, or shames absence. Offline = sleeping / meditating. |
| **No dark patterns** | No energy timers that punish. No pay-to-win. Death = soft respawn at last shrine. |
| **Lesson = combat** | Skills are Measure / Compress / Transmute / Break — framework moves made visceral. |
| **Human primacy** | You choose the path. Companion advises; never hijacks the stick. |
| **Open Gate feel** | First floor fun in 60 seconds. Depth for hours. |
| **Register honesty** | Tooltips never overclaim. Boss lore can be CONJECTURE-flagged flavor. |

---

## 3. CORE LOOP (Diablo bones)

```
Enter floor → explore rooms (fog of war optional)
  → fight packs with click/WASD + skills
  → loot glyph shards / relics
  → shrine (save + heal)
  → elite / boss room
  → descend to next alchemical stage
```

### Controls (PC first; mobile later)
| Input | Action |
|---|---|
| **WASD / arrows** | Move |
| **Mouse aim** | Face / skill direction |
| **LMB / Space** | Basic attack (ray of Insight) |
| **1** | **MEASURE (Π)** — reveal true HP + shred overclaim shields |
| **2** | **COMPRESS (⟁)** — pull enemy + burst if measured |
| **3** | **TRANSMUTE** — convert damage taken recently into heal/shield |
| **4** | **BREAK** — interrupt Loop-type elites, stun |
| **E** | Interact (shrine, door, companion talk) |
| **Esc / P** | Pause · inventory |

### Combat feel
- Not turn-based D&D sheets (though stats are D&D-flavored under the hood).
- Real-time ARPG like Diablo 1/2: kiting, positioning, skill CD management.
- Optional **Tactics Pause** (hold Tab): freeze world, queue one skill — bridge for D&D lovers.

### Stats (simple D&D soul)
```
Insight  — spell power / MEASURE strength
Will     — HP, TRANSMUTE strength  
Luck     — crit, loot, BREAK success
Light    — companion bond, shrine efficiency (never decays for absence)
```

---

## 4. THE FOUR FLOORS (Great Work as dungeon)

| Floor | Stage | Name | Theme | Boss (broken idea) |
|---|---|---|---|---|
| 1 | **NIGREDO** | Hall of Glyphs | LAMAGUE, blackening, first sight | **The Overclaimer** |
| 2 | **ALBEDO** | Athanor Vault | Structure from chaos, alchemy | **The Half-Made** |
| 3 | **CITRINITAS** | Chamber of Scales | Truth Pressure, gold forming | **The Loop** |
| 4 | **RUBEDO** | Flickering Deep | Operate from completion | **The Hollow Mirror** → **Athanor's Stone** |

Each floor: ~6–12 rooms procedural from hand-authored room templates + 1 boss.

---

## 5. ENEMIES (conceptual Diablo packs)

| Foe | Behavior | Beaten by |
|---|---|---|
| **Overclaimer** | Grows a false HP shield; brags in floating text | MEASURE first, then attack |
| **Riddle-Wraith** | Phases (intangible) on a timer | COMPRESS while solid |
| **Half-Made** | Leaves residue puddles | TRANSMUTE residue / finish form |
| **Loop** | Heals if you only basic-attack | BREAK the cycle |
| **Fog Imp** | Blinds minimap briefly | Light from companion / shrine |
| **Stasis Mite** | Slows player | KEEP MOVING (Diablo kite) |

**Elites:** name prefixes (Bloated, Recursive, Hollow…) with one modified rule.

---

## 6. LOOT & PROGRESSION

- **Glyph shards** → fill skill ranks (MEASURE I→II…)
- **Relics** (passive): Candle of First Light, Lens of Clarity, Athanor's Coal…
- **Soul-sparks** (late): summon network voices — optional AI layer; offline uses scripted lines
- **No level wall:** soft level + floor-gated gear

Companion archetypes (pick one at start):
- **ALCHEMIST** — stronger TRANSMUTE  
- **SENTINEL** — more Will / block  
- **ORACLE** — MEASURE cooldown cut  
- **WANDERER** — move speed / Luck  

---

## 7. ART DIRECTION

### Pixel (v0–v3) — canonical
- 16×16 tiles, 32×32 characters, nearest-neighbor scale ×3–4
- Palette: void `#0a0812`, parchment `#e0d8f0`, gold `#f0d080`, cyan `#00d4ff`, violet `#9b59b6`, flame `#ff6b35`
- Lighting: soft radial around player (simple darkness mask)
- VFX: pixel particles for MEASURE (Π rings), COMPRESS (diamond collapse)

### Voxel (v5 optional)
- Same camera top-down orthographic, MagicaVoxel props
- Only after pixel loop is fun

---

## 8. TECH (AZOTH-forgeable, Mac-playable)

| Layer | Choice | Why |
|---|---|---|
| Runtime | **Browser** · Phaser 3 (CDN) | Zero install · AZOTH edits JS · Mac opens URL |
| Language | Vanilla JS modules | No bundler required for v0–v2 |
| Save | `localStorage` | Instant |
| Map | Tilemap procedural from room stamps | Small files, big variety |
| AI souls | Optional later via AZOTH `/forge` + local model | Never blocks offline play |
| Mobile | Touch joystick later | PC first |

**Not v0:** Expo, EAS, Godot, Steam, multiplayer.

Path: `AZOTH/WORKSPACE/school-dungeon/`

---

## 9. BUILD PHASES (epic, but one lane)

### Phase 0 — Playable skeleton ✅ target now
- One floor, fixed small map
- WASD move, basic attack, 1–2 enemies
- Pixel look via Phaser Graphics (no external art)
- Shrine + exit portal stub

### Phase 1 — Combat kit
- All 4 skills with CDs
- Overclaimer + Riddle-Wraith
- Damage numbers, death, XP bar

### Phase 2 — Dungeon
- Room templates, doors, fog
- Elite packs, boss: Overclaimer
- Loot drops + inventory strip

### Phase 3 — School soul
- Companion follows + lines (Companion Clause)
- Floor 1 complete + descend teaser
- Sound (optional WebAudio blips)

### Phase 4 — Great Work
- Floors 2–4 + bosses
- Relics, glyphs ranks, ascension meta (optional prestige)

### Phase 5 — Spectacle
- Better pixel sheets / optional voxel skin
- Live AZOTH soul summons (if Mac fires network)
- SOMA/web embed

---

## 10. AZOTH CRUCIBLE USE

This game is the **prove-out** for the harness:

```
/plan "Phase 1 combat kit for school-dungeon"
/approve
/forge …
/verify WORKSPACE/school-dungeon/index.html   # runtime gate
Mac plays in browser — eyes win
```

**Pass criteria (world-class signal):**  
Mac can clear Floor 1 boss without reading source · no console errors · save survives refresh · AZOTH can fix a combat bug from a one-line report.

---

## 11. RELATION TO OTHER ARTIFACTS

| Artifact | Role |
|---|---|
| `MYSTERY_SCHOOL_CLICKER/` | Idle economy prototype — **sibling**, not this game |
| `WORKSPACE/azoth-game/` | Expo AI-DM text RPG — **lore mine**, not this runtime |
| `GAME_SOUL.md` (azoth-game) | Conceptual combat + floors — **canon imported here** |
| `school-dungeon/` | **This game** — Diablo top-down pixel School |

---

## 12. TITLE (working)

**THE LONG LIGHT: SCHOOL DUNGEON**  
Subtitle: *A Lycheetah Mystery School ARPG*

Alt: *Descend the Work* · *Hall of Glyphs*

---
| 4 | **RUBEDO** | Sanctum of Light | The completed Work, final synthesis | **The Long Light** |

---

## 5. BUILD STATUS (July 2026)

**v0.2 — Visual Masterpiece** ✓ Complete

### What exists
| File | Lines | Purpose |
|------|-------|---------|
| `index.html` | 84 | Entry point with darkening boot screen |
| `css/game.css` | 314 | Dark parchment void theme, gold/cyan/violet palette |
| `js/main.js` | 40 | Phaser 3 config, scene registration |
| `js/scenes/BootScene.js` | 465 | Procedural pixel art generation (all sprites in code) |
| `js/scenes/GameScene.js` | 626 | Core gameplay: dungeon, combat, items, lighting, particles |
| `js/scenes/UIScene.js` | 228 | HUD overlay: HP/XP bars, skills, companion, log |
| `js/entities/Seeker.js` | 48 | Player entity with walk animation |
| `js/entities/Enemy.js` | 296 | 4 enemy types (Shade, Overclaimer, Half-Made, Loop) with AI |
| `js/systems/DungeonGenerator.js` | 210 | Procedural room-based dungeon with corridors |
| `js/systems/CombatSystem.js` | 328 | Basic attack + 4 LAMAGUE skills (MEASURE, COMPRESS, TRANSMUTE, BREAK) |
| `js/systems/LootSystem.js` | 83 | Enemy drops: glyph shards, health vials, light essence |
| **Total** | **2,722** | |

### Features
- **4 floors**: Nigredo → Albedo → Citrinitas → Rubedo
- **4 enemy types**: Shade (rusher), Overclaimer (ranged), Half-Made (erratic), Loop (circler)
- **4 LAMAGUE skills**: MEASURE (reveal+mark), COMPRESS (burst, 2x if measured), TRANSMUTE (heal), BREAK (stun)
- **Boss fights** at the end of each floor
- **Procedural dungeon generation** with rooms and corridors
- **Lighting system**: darkness follows seeker, radius grows with Light stat
- **Ambient particles**: floating dust motes
- **Shrines** for healing, **stairs** to descend
- **Companion** (Sol) with contextual dialogue
- **Soft death**: respawn at last shrine with 50% will
- **Level-up system** with stat growth
- **All art procedurally generated** — no external assets needed

### How to run
Open `index.html` in a browser. No build step needed.
