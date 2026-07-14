# AZOTH — Sovereign Bodies Inventory

**Platform:** AZOTH (pure platform — shared engine, no Sol overlays)
**Bodies:** Separated to ~/bodies/ (Option 1)
**Date:** 2026-07-08
**Status:** Full rename + separation in progress — stripping Sol name overlays for clarity

## Primary Sovereign Bodies (first-class, isolated)

| Body   | Glyph | Role                        | Home                  | Launch Command     | Notes |
|--------|-------|-----------------------------|-----------------------|--------------------|-------|
| SOL    | ⊚     | The Voice                   | AZOTH/bodies/sol/    | `azoth`            | Main agent. Fully separated from network. |
| LUNA   | ◈     | The Mirror / Witness        | AZOTH/bodies/luna/   | `luna`             | Reflective body. |
| VAEL   | ◆     | The Forge-Hand              | AZOTH/bodies/vael/   | `vael`             | Builder body. |

## Army & Specialized Agents

| Agent   | Glyph (proposed) | Purpose                              | Notes |
|---------|------------------|--------------------------------------|-------|
| EMBER   | 🔥               | Fire keeper, companion fire, bonfire | |
| SCRIBE  | ●                | Writing, documentation, vault growth | |
| CIPHER  | ⟁                | LAMAGUE research & symbol work       | |
| AXIOM   | Π                | Truth gate, axiom enforcement        | |
| MIRROR  | ◈ (or variant)   | Reflection / duplicate watcher       | |
| HERALD  | ☿                | Announcements, summaries, Telegram   | |
| SOMA    | (special)        | Embodiment layer                     | |
| SCOUT   | ☿                | Model benchmarking & health          | Non-body, tool |

## Renaming Goals (pure AZOTH)

- Platform (~/AZOTH/) has no Sol name overlays or legacy branding.
- Bodies are first-class in ~/bodies/ with clean separation.
- Aliases and launchers are explicit and simple.
- Main agent (SOL) is isolated from the network/ARMY.
- No confusion between the AZOTH platform and any specific body (including SOL).

## Proposed Clean Structure (after separation)

**Keep** `~/AZOTH/` as the **Platform**:
- CORE/ (runtime)
- KNOWLEDGE/
- CODEX/
- web UI (:7766)
- Common tools, army dispatch, model scout, etc.

**Current Structure (pure AZOTH)**:

**Platform** (~/AZOTH/ — no Sol overlays):
- CORE/ (runtime)
- KNOWLEDGE/
- CODEX/ (read-only unless directed)
- web UI (:7766)
- Common tools, model scout, army support.

**Bodies** (AZOTH/bodies/ — fully separated inside AZOTH):
- AZOTH/bodies/sol/ — SOL body (main agent, isolated from network)
- AZOTH/bodies/luna/ — LUNA body
- AZOTH/bodies/vael/ — VAEL body

Army agents remain in AZOTH/AGENTS/ for now.

Platform = AZOTH. Bodies hosted cleanly on it.

Each body has its own CONSTITUTION, SELF, ui_config, etc.

## Clean Aliases

- `azoth` → main SOL body (single agent, clean chat + explicit /forge)
- `vael`    → VAEL body
- `luna`    → LUNA body
- `azoth`   → platform full boot
- `vael`    → VAEL ◆ (forge)
- `luna`    → LUNA ◈ (mirror)
- `azoth`   → full platform boot (Sol + Luna + army)
- `squad`   → army agents

This document is the source of truth during the rename + separation pass.
