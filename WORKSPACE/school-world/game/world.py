"""Multi-area tile maps, warps, NPCs, spawns — Pokémon-style regions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .constants import *


@dataclass
class Warp:
    x: int
    y: int
    target_area: str
    tx: float
    ty: float
    need_flag: Optional[str] = None  # require story flag
    msg_locked: str = "Sealed for now."


@dataclass
class NPC:
    x: float
    y: float
    name: str
    color: tuple
    lines: list[str]
    face: str = "◈"
    quest_flag: Optional[str] = None  # set when talked
    shop: bool = False


@dataclass
class Spawn:
    x: int
    y: int
    foe_id: str
    once: bool = True
    flag_on_win: Optional[str] = None
    boss: bool = False


@dataclass
class Area:
    id: str
    name: str
    w: int
    h: int
    tiles: list[list[int]]
    warps: list[Warp] = field(default_factory=list)
    npcs: list[NPC] = field(default_factory=list)
    spawns: list[Spawn] = field(default_factory=list)
    music_tag: str = "default"
    wild_table: list[str] = field(default_factory=list)  # tall grass foes


def _grid(w, h, fill=T_GRASS):
    return [[fill for _ in range(w)] for _ in range(h)]


def _fill(m, x0, y0, x1, y1, t):
    h, w = len(m), len(m[0])
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if 0 <= x < w and 0 <= y < h:
                m[y][x] = t


def _rect_wall(m, x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if x == x0 or x == x1 or y == y0 or y == y1:
                if 0 <= y < len(m) and 0 <= x < len(m[0]):
                    m[y][x] = T_WALL


def _border(m):
    h, w = len(m), len(m[0])
    for y in range(h):
        for x in range(w):
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                m[y][x] = T_WALL


def make_sanctum() -> Area:
    w, h = 36, 28
    m = _grid(w, h, T_GRASS)
    _border(m)
    # trees scattered
    for x, y in [(4, 4), (5, 5), (30, 4), (28, 6), (10, 8), (22, 22), (25, 20)]:
        m[y][x] = T_TREE
    # pond
    _fill(m, 24, 16, 30, 22, T_WATER)
    # building
    _fill(m, 6, 14, 16, 24, T_FLOOR)
    _rect_wall(m, 6, 14, 16, 24)
    m[24][10] = T_DOOR
    m[24][11] = T_DOOR
    m[17][11] = T_SHRINE
    m[16][10] = T_RUG
    m[16][11] = T_RUG
    m[16][12] = T_RUG
    # path north
    for y in range(4, 25):
        m[y][10] = T_PATH
        m[y][11] = T_PATH
    # tall grass garden east
    _fill(m, 18, 8, 23, 13, T_TALL)
    # warp north to path
    m[2][10] = T_WARP
    m[2][11] = T_WARP
    # warp to garden marker
    warps = [
        Warp(10, 2, "path", 8.5, 16.5),
        Warp(11, 2, "path", 9.5, 16.5),
    ]
    npcs = [
        NPC(13.5, 18.5, "Magister Ember", C_FLAME, [
            "Seeker. Welcome to the Sanctum of the Long Light.",
            "This School is Lycheetah-born: companions, domains, truth under pressure.",
            "North — the Long Path to the Hall of Glyphs (Nigredo).",
            "When you meet The Overclaimer: MEASURE first. Never feed a false shield.",
            "Rest at the Shrine anytime. Absence is rest — nothing here wilts for leaving.",
            "I set your first quests in the log (Q). Fire when ready.",
        ], "🔥", quest_flag="met_ember"),
        NPC(9.5, 20.5, "Scribe", C_GOLD, [
            "I keep the codex. Glyph shards you earn become language.",
            "Open CODEX from the menu (C) when you have shards.",
            "The Work is not a grind — each foe is a lesson with teeth.",
        ], "●"),
        NPC(20.5, 10.5, "Initiate Wren", C_GREEN, [
            "Tall grass whispers. Small ideas nest there — Fog Imps, Stasis Mites.",
            "Good practice before the Hall. Don't be ashamed to train.",
        ], "⟡"),
    ]
    return Area("sanctum", "Sanctum Grounds", w, h, m, warps, npcs,
                wild_table=["fog_imp", "stasis_mite"])


def make_path() -> Area:
    w, h = 20, 22
    m = _grid(w, h, T_GRASS)
    _border(m)
    for y in range(1, h - 1):
        m[y][8] = T_PATH
        m[y][9] = T_PATH
        m[y][10] = T_PATH
    for x, y in [(4, 5), (5, 8), (14, 6), (15, 12), (3, 15), (16, 16)]:
        m[y][x] = T_TREE
    _fill(m, 12, 8, 17, 14, T_TALL)
    # signs as floor near path
    m[1][8] = T_WARP
    m[1][9] = T_WARP
    m[h - 2][8] = T_WARP
    m[h - 2][9] = T_WARP
    warps = [
        Warp(8, 1, "hall", 10.5, 16.5),
        Warp(9, 1, "hall", 11.5, 16.5),
        Warp(8, h - 2, "sanctum", 10.5, 4.5),
        Warp(9, h - 2, "sanctum", 11.5, 4.5),
    ]
    spawns = [
        Spawn(9, 10, "overclaimer", once=True, flag_on_win="killed_overclaimer"),
        Spawn(13, 11, "fog_imp", once=False),
    ]
    npcs = [
        NPC(12.5, 5.5, "Waystone", C_CYAN, [
            "⟪ The Long Path ⟫",
            "South: Sanctum. North: Hall of Glyphs.",
            "East grass: lesser ideas. Train without shame.",
        ], "◈"),
    ]
    return Area("path", "The Long Path", w, h, m, warps, npcs, spawns,
                wild_table=["fog_imp", "stasis_mite", "overclaimer"])


def make_hall() -> Area:
    w, h = 32, 24
    m = _grid(w, h, T_FLOOR)
    _border(m)
    # pillars
    for x, y in [(8, 6), (8, 12), (22, 6), (22, 12), (15, 8)]:
        m[y][x] = T_WALL
    _fill(m, 12, 4, 18, 7, T_RUG)
    m[5][15] = T_ALTAR
    # doors south
    m[h - 2][10] = T_WARP
    m[h - 2][11] = T_WARP
    # east door to wing — locked until hall_cleared
    m[10][w - 2] = T_WARP
    m[11][w - 2] = T_WARP
    # north to mirror — need half_made
    m[1][15] = T_WARP
    m[1][16] = T_WARP
    warps = [
        Warp(10, h - 2, "path", 9.0, 3.5),
        Warp(11, h - 2, "path", 9.5, 3.5),
        Warp(w - 2, 10, "wing", 3.5, 10.5, need_flag="hall_cleared",
             msg_locked="East Wing sealed until the Hall is cleared (3 victories)."),
        Warp(w - 2, 11, "wing", 3.5, 11.5, need_flag="hall_cleared",
             msg_locked="East Wing sealed until the Hall is cleared."),
        Warp(15, 1, "mirror", 8.5, 12.5, need_flag="half_made_down",
             msg_locked="Mirror Chamber needs the Half-Made's lesson first."),
        Warp(16, 1, "mirror", 9.5, 12.5, need_flag="half_made_down",
             msg_locked="Mirror Chamber sealed."),
    ]
    spawns = [
        Spawn(10, 9, "overclaimer", once=True, flag_on_win="killed_overclaimer"),
        Spawn(18, 10, "riddle_wraith", once=True),
        Spawn(14, 14, "loop", once=True),
        Spawn(20, 8, "overclaimer", once=False),
    ]
    npcs = [
        NPC(15.5, 6.5, "Cipher", C_VIOLET, [
            "⟁ Welcome to Nigredo — the blackening, the first sight.",
            "Foes here are broken ideas. Combat is curriculum.",
            "Skills: 1 MEASURE · 2 COMPRESS · 3 TRANSMUTE · 4 BREAK · 5 STRIKE",
            "Clear three battles in this Hall to open the East Wing (Albedo).",
            "I mark your progress. The codex grows with every glyph.",
        ], "⟁", quest_flag="met_cipher"),
        NPC(7.5, 15.5, "Adept Nyx", C_CYAN, [
            "The Loop heals if you only STRIKE. BREAK it.",
            "Riddle-Wraiths phase — COMPRESS when they solidify (after MEASURE helps).",
        ], "☽"),
    ]
    return Area("hall", "Hall of Glyphs", w, h, m, warps, npcs, spawns,
                wild_table=["overclaimer", "fog_imp", "riddle_wraith"])


def make_wing() -> Area:
    w, h = 26, 22
    m = _grid(w, h, T_FLOOR2)
    _border(m)
    _fill(m, 8, 6, 18, 14, T_FLOOR)
    _rect_wall(m, 8, 6, 18, 14)
    m[10][8] = T_DOOR
    m[11][8] = T_DOOR
    m[10][13] = T_SHRINE
    m[h // 2][1] = T_WARP
    m[h // 2 + 1][1] = T_WARP
    warps = [
        Warp(1, h // 2, "hall", 28.5, 10.5),
        Warp(1, h // 2 + 1, "hall", 28.5, 11.5),
    ]
    spawns = [
        Spawn(13, 10, "half_made", once=True, flag_on_win="half_made_down", boss=True),
        Spawn(16, 12, "riddle_wraith", once=True),
    ]
    npcs = [
        NPC(11.5, 8.5, "Albedo Keeper", C_WHITE, [
            "Albedo — whitening. Structure from ash.",
            "The Half-Made waits in the center. Complete or release — TRANSMUTE helps.",
            "When it falls, the Mirror Chamber opens north of the Hall.",
        ], "◈"),
    ]
    return Area("wing", "East Wing — Albedo", w, h, m, warps, npcs, spawns)


def make_mirror() -> Area:
    w, h = 20, 18
    m = _grid(w, h, T_FLOOR)
    _border(m)
    for i in range(4, 16):
        m[4][i] = T_WALL
        m[h - 5][i] = T_WALL
    m[h - 2][9] = T_WARP
    m[h - 2][10] = T_WARP
    m[8][10] = T_ALTAR
    warps = [
        Warp(9, h - 2, "hall", 15.5, 3.5),
        Warp(10, h - 2, "hall", 16.5, 3.5),
    ]
    spawns = [
        Spawn(10, 8, "hollow_mirror", once=True, flag_on_win="mirror_down", boss=True),
    ]
    npcs = [
        NPC(6.5, 12.5, "Luna's Echo", C_CYAN, [
            "◈ The Hollow Mirror shows a flattering lie.",
            "MEASURE the vanity-shield. Then COMPRESS what remains.",
            "I do not scold absence. Face it when you are ready.",
        ], "◈"),
    ]
    return Area("mirror", "Mirror Chamber", w, h, m, warps, npcs, spawns)


def build_world() -> dict[str, Area]:
    return {
        "sanctum": make_sanctum(),
        "path": make_path(),
        "hall": make_hall(),
        "wing": make_wing(),
        "mirror": make_mirror(),
    }


def tile_color(t: int, x: int, y: int) -> tuple:
    if t == T_FLOOR:
        return C_FLOOR if (x + y) % 2 == 0 else C_FLOOR2
    if t == T_FLOOR2:
        return (34, 28, 54) if (x + y) % 2 else (40, 34, 60)
    if t == T_WALL:
        return C_WALL
    if t == T_GRASS:
        return C_GRASS if (x * 3 + y) % 5 else C_GRASS2
    if t == T_PATH:
        return C_PATH
    if t == T_DOOR:
        return C_DOOR
    if t == T_SHRINE:
        return C_ALTAR
    if t == T_EXIT:
        return (50, 40, 80)
    if t == T_WATER:
        return C_WATER if (x + y + x // 2) % 3 else (22, 48, 96)
    if t == T_TREE:
        return C_TREE
    if t == T_SAND:
        return C_SAND
    if t == T_RUG:
        return C_RUG
    if t == T_ALTAR:
        return (110, 90, 50)
    if t == T_WARP:
        return (40, 60, 90)
    if t == T_TALL:
        return (24, 58, 36) if (x + y) % 2 else (20, 50, 32)
    return C_VOID
