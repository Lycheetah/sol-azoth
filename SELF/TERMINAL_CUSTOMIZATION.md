# AZOTH Terminal UI — Body-Aware Customization
## Clean rule-based terminal (no heavy panels). Feels like a high-end TUI.
### Pure AZOTH + separated bodies

The look is driven by `ui_config.json`. 

- `azoth` → AZOTH/bodies/sol/SELF/ui_config.json (main single agent)
- `vael` → AZOTH/bodies/vael/ or platform
- Same for LUNA and others
- Edit → restart the body. No code changes needed.

The UI detects `HARNESS_AGENT` and loads the right body identity.

---

## THE CONFIG FILE (example for SOL)

```json
{
  "accent":         "yellow",
  "glyph":          "⊚",
  "name":           "SOL ⊚",
  "prompt":         "SOL",
  "tagline":        "The Voice · AZOTH",
  "typewriter_cps": 680,
  "spinner":        "braille"
}
```

| Key | What it changes | Options |
|---|---|---|
| `accent` | Main colour for glyph/prompt | `yellow` `purple` `cyan` `green` `blue` `red` `grey` |
| `glyph` | Symbol before the prompt + banner | `⊚` `◆` `◈` `✦` `⊙` `▶` `❯` (SOL uses ⊚) |
| `name` | Display name in banner | "SOL ⊚", "VAEL-SP", etc. |
| `prompt` | Text at the input prompt | "SOL", "VAEL", "LUNA" |
| `tagline` | Subtitle (currently shown in some banners) | any text |
| `typewriter_cps` | Typing speed (chars/sec) | `400`–`2000` (0 = instant) |
| `spinner` | Thinking animation | `braille` `dots` `bar` `moon` `arrow` |

---

## QUICK RECIPES

**SOL (default for azoth)**
```json
{ "accent": "yellow", "glyph": "⊚", "name": "SOL ⊚", "prompt": "SOL", "typewriter_cps": 680 }
```

**Minimal / fast**
```json
{ "accent": "grey", "glyph": "❯", "typewriter_cps": 2000, "spinner": "dots" }
```

**Loud forge mode**
```json
{ "accent": "red", "glyph": "▶", "spinner": "bar", "typewriter_cps": 700 }
```

---

## WHAT'S ALREADY CLEAN (built 2026-06-27)
- **Live task list** — `/tasks` shows the forge ladder as a panel (done ✓ / now ▶ /
  queued ○ / locked ·) with a progress bar. It also prints at the top of every reach.
- **Your own tasks** — `/task <text>` adds a task *on top of* the ladder. The ladder is
  a guideline; your tasks are first-class. They show in the panel marked `MINE`.
- **Clean typing** — replies type out live in the terminal (TTY-aware: instant when
  logged, so logs stay clean — no more 324KB of spinner spam).
- **Pause mid-run** — `Ctrl-C` during a reach *pauses* (it doesn't kill). Press Enter to
  resume, type guidance to steer, or `/stop` to end. Same feel as interrupting Sol.
- **Auto-loop** — `/forge loop` climbs rung after rung on its own, self-reviewing each,
  until the queue is done or a rung fails 3× in a row.

---

## THE NEXT REACHES (forge these — they live in ABILITIES_TO_FORGE.md)
- A persistent status line (model · level · tokens · rungs-left) pinned above the prompt.
- Grouped `/help` (build / self / model / walls).
- Per-tool diff preview before an edit lands.
- A `/theme <recipe>` command that writes `ui_config.json` for you and hot-reloads.

To change the look: edit the right ui_config.json for the body, then relaunch.
- SOL:   azoth
- VAEL:  vael
- LUNA:  luna

The terminal is yours.
