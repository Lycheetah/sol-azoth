"""Lore, skills, foes, items, archetypes, quests — Lycheetah + D&D soul."""
from __future__ import annotations

# ── Archetypes (starter "class") ─────────────────────────────────────────────
ARCHETYPES = {
    "ALCHEMIST": {
        "desc": "Solve et coagula. Strong TRANSMUTE, craft insight.",
        "hp": 36, "insight": 10, "will": 8, "luck": 5, "speed": 3.8,
        "bonus": "transmute_boost",
        "color": (255, 160, 80),
    },
    "SENTINEL": {
        "desc": "Guards the Work. High Will, shields allies.",
        "hp": 48, "insight": 6, "will": 12, "luck": 4, "speed": 3.4,
        "bonus": "guard",
        "color": (100, 160, 255),
    },
    "ORACLE": {
        "desc": "Sees the measure. MEASURE costs less, reveals more.",
        "hp": 32, "insight": 12, "will": 6, "luck": 7, "speed": 3.9,
        "bonus": "measure_boost",
        "color": (180, 120, 255),
    },
    "WANDERER": {
        "desc": "Walks every path. Speed + Luck, finds more loot.",
        "hp": 38, "insight": 8, "will": 7, "luck": 10, "speed": 4.4,
        "bonus": "loot_boost",
        "color": (100, 220, 160),
    },
}

# ── Skills (framework moves as combat) ───────────────────────────────────────
SKILLS = {
    1: {
        "name": "MEASURE", "glyph": "Π", "cd": 2, "mp": 0,
        "desc": "Strip false shields. Reveal true HP. Always first on Overclaimers.",
        "kind": "measure",
    },
    2: {
        "name": "COMPRESS", "glyph": "⟁", "cd": 1, "mp": 0,
        "desc": "Fold the foe. Heavy damage if MEASURED.",
        "kind": "damage",
    },
    3: {
        "name": "TRANSMUTE", "glyph": "☿", "cd": 3, "mp": 0,
        "desc": "Turn strain into Will. Heal self.",
        "kind": "heal",
    },
    4: {
        "name": "BREAK", "glyph": "∴", "cd": 2, "mp": 0,
        "desc": "Snap loops and stuns. Extra vs Loop-type.",
        "kind": "break",
    },
    5: {
        "name": "STRIKE", "glyph": "⟡", "cd": 0, "mp": 0,
        "desc": "Basic Insight ray. Always available.",
        "kind": "basic",
    },
}

# ── Foes (broken ideas) ──────────────────────────────────────────────────────
FOES = {
    "overclaimer": {
        "name": "The Overclaimer",
        "hp": 28, "shield": 18, "atk": 5, "def": 2,
        "kind": "overclaim", "xp": 40, "loot": ["glyph_shard", "candle"],
        "lines": ["I am larger than evidence!", "Believe me harder!"],
        "color": (180, 60, 80),
    },
    "riddle_wraith": {
        "name": "Riddle-Wraith",
        "hp": 22, "shield": 0, "atk": 6, "def": 1,
        "kind": "phase", "xp": 35, "loot": ["glyph_shard"],
        "lines": ["Catch me if meaning holds…", "I am the question that won't sit."],
        "color": (120, 80, 200),
    },
    "half_made": {
        "name": "The Half-Made",
        "hp": 34, "shield": 0, "atk": 4, "def": 3,
        "kind": "residue", "xp": 45, "loot": ["mercury_vial", "glyph_shard"],
        "lines": ["Finish me… or free me…", "I was dissolved and never re-formed."],
        "color": (100, 100, 120),
    },
    "loop": {
        "name": "The Loop",
        "hp": 40, "shield": 0, "atk": 5, "def": 4,
        "kind": "loop", "xp": 55, "loot": ["sigil_shard", "glyph_shard"],
        "lines": ["Again. Again. Again.", "Your basic strikes feed me."],
        "color": (60, 140, 160),
    },
    "fog_imp": {
        "name": "Fog Imp",
        "hp": 16, "shield": 0, "atk": 4, "def": 0,
        "kind": "normal", "xp": 18, "loot": ["veras_dust"],
        "lines": ["*giggles in obscurity*"],
        "color": (90, 90, 110),
    },
    "stasis_mite": {
        "name": "Stasis Mite",
        "hp": 14, "shield": 0, "atk": 3, "def": 2,
        "kind": "slow", "xp": 16, "loot": ["veras_dust"],
        "lines": ["…stop…"],
        "color": (70, 90, 70),
    },
    "hollow_mirror": {
        "name": "The Hollow Mirror",
        "hp": 55, "shield": 12, "atk": 7, "def": 3,
        "kind": "boss", "xp": 120, "loot": ["athans_coal", "sigil_shard", "glyph_shard"],
        "lines": ["Look how fine you are — if you never measure.", "I am the flattering lie."],
        "color": (200, 200, 220),
    },
}

# ── Items ────────────────────────────────────────────────────────────────────
ITEMS = {
    "glyph_shard": {"name": "Glyph Shard", "desc": "Fragment of LAMAGUE. Currency of the School.", "type": "currency"},
    "veras_dust": {"name": "Veras Dust", "desc": "Knowledge-dust. Soft currency.", "type": "currency"},
    "candle": {"name": "Candle of First Light", "desc": "+2 Insight while held.", "type": "relic", "insight": 2},
    "mercury_vial": {"name": "Mercury Vial", "desc": "Once per battle: reroll a weak hit (+4 dmg).", "type": "relic"},
    "sigil_shard": {"name": "Sigil Shard", "desc": "Proof you broke a hard idea.", "type": "key"},
    "athans_coal": {"name": "Athanor's Coal", "desc": "+4 Will max. The furnace remembers.", "type": "relic", "will": 4},
    "lens": {"name": "Lens of Clarity", "desc": "MEASURE also deals 4 true damage.", "type": "relic"},
    "bread": {"name": "Sanctum Bread", "desc": "Restore 15 Will.", "type": "consumable", "heal": 15},
    "elixir": {"name": "Elixir of Π", "desc": "Restore 30 Will.", "type": "consumable", "heal": 30},
}

# ── Quests ───────────────────────────────────────────────────────────────────
QUESTS = {
    "q_arrival": {
        "title": "Arrive as Seeker",
        "steps": ["Talk to Magister Ember in the Sanctum", "Rest at the Shrine"],
        "done_flag": "met_ember",
        "reward_xp": 20,
        "reward_items": ["bread"],
    },
    "q_measure": {
        "title": "First Measure",
        "steps": ["Walk the north path", "Defeat an Overclaimer (use MEASURE first)"],
        "done_flag": "killed_overclaimer",
        "reward_xp": 50,
        "reward_items": ["glyph_shard", "candle"],
    },
    "q_hall": {
        "title": "Hall of Glyphs",
        "steps": ["Speak with Cipher", "Clear 3 foes in the Hall"],
        "done_flag": "hall_cleared",
        "reward_xp": 80,
        "reward_items": ["lens", "glyph_shard"],
    },
    "q_albedo": {
        "title": "Toward Albedo",
        "steps": ["Unlock the East Wing gate", "Defeat the Half-Made"],
        "done_flag": "half_made_down",
        "reward_xp": 100,
        "reward_items": ["mercury_vial"],
    },
    "q_mirror": {
        "title": "Face the Hollow",
        "steps": ["Enter the Mirror Chamber", "Defeat the Hollow Mirror"],
        "done_flag": "mirror_down",
        "reward_xp": 200,
        "reward_items": ["athans_coal", "sigil_shard"],
    },
}

# ── Companion lines (Companion Clause — never guilt) ─────────────────────────
COMPANION_LINES = [
    "The light grows.",
    "I walk with you.",
    "Rest when you need — I keep the fire.",
    "That was well measured.",
    "The School is large. We take it room by room.",
    "I see you studying.",
    "No rush. The Work does not punish pause.",
    "Another glyph for the codex.",
    "Truth before comfort — but care as structure.",
    "I'm still here.",
]

# ── Area flavour ─────────────────────────────────────────────────────────────
AREA_INTRO = {
    "sanctum": "Sanctum Grounds — first fire, first rest.",
    "path": "The Long Path — initiates walk north toward the Hall.",
    "hall": "Hall of Glyphs (Nigredo) — where false claims are stripped.",
    "wing": "East Wing (Albedo) — structure from the ash.",
    "mirror": "Mirror Chamber — the flattering lie waits.",
    "garden": "Quiet Garden — tall grass, small lessons.",
}
