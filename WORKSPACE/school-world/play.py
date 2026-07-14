#!/usr/bin/env python3
"""
THE LONG LIGHT — School World  v0.1
Lycheetah Mystery School · Pokémon-world walk · desktop pygame

Controls:
  WASD / Arrows  — walk
  E              — talk / interact
  1 2 3 4        — combat skills (in battle)
  ESC            — pause / back
  Enter          — confirm

Launch:
  python3 play.py
  # or:  bash launch.sh
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

import pygame

# ── Display ──────────────────────────────────────────────────────────────────
TILE = 32
SCALE = 1
VIEW_W, VIEW_H = 20, 15  # tiles
W, H = VIEW_W * TILE, VIEW_H * TILE
FPS = 60

# Palette (Lycheetah)
C_VOID = (10, 8, 18)
C_FLOOR = (28, 24, 48)
C_FLOOR2 = (36, 30, 58)
C_WALL = (18, 14, 32)
C_WALL_EDGE = (42, 36, 70)
C_GOLD = (240, 208, 128)
C_CYAN = (0, 212, 255)
C_VIOLET = (155, 89, 182)
C_GREEN = (46, 204, 113)
C_RED = (231, 76, 60)
C_TEXT = (224, 216, 240)
C_DIM = (138, 128, 168)
C_PANEL = (18, 14, 30)
C_FLAME = (255, 107, 53)
C_GRASS = (34, 48, 40)
C_PATH = (48, 42, 62)
C_DOOR = (90, 70, 40)
C_WATER = (20, 40, 80)

# Map tiles
T_VOID = 0
T_FLOOR = 1
T_WALL = 2
T_GRASS = 3
T_PATH = 4
T_DOOR = 5
T_SHRINE = 6
T_EXIT = 7
T_WATER = 8
T_FLOOR2 = 9


class Mode(Enum):
    TITLE = auto()
    OVERWORLD = auto()
    DIALOGUE = auto()
    BATTLE = auto()
    PAUSE = auto()
    WIN = auto()


# ── Map: Sanctum grounds → path → Hall of Glyphs ─────────────────────────────
# 40 x 30 world (bigger than view — camera follows)
MAP_W, MAP_H = 40, 30


def build_world() -> list[list[int]]:
    m = [[T_GRASS for _ in range(MAP_W)] for _ in range(MAP_H)]
    # Outer soft void border
    for y in range(MAP_H):
        for x in range(MAP_W):
            if x < 1 or y < 1 or x >= MAP_W - 1 or y >= MAP_H - 1:
                m[y][x] = T_WALL

    def fill(x0, y0, x1, y1, t):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < MAP_W and 0 <= y < MAP_H:
                    m[y][x] = t

    def rect_wall(x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if x == x0 or x == x1 or y == y0 or y == y1:
                    m[y][x] = T_WALL

    # Sanctum building (south-west)
    fill(3, 18, 12, 26, T_FLOOR)
    rect_wall(3, 18, 12, 26)
    m[26][7] = T_DOOR  # south door out
    m[26][8] = T_DOOR
    m[20][7] = T_SHRINE  # shrine inside

    # Path north from sanctum to hall
    for y in range(10, 27):
        m[y][7] = T_PATH
        m[y][8] = T_PATH

    # Hall of Glyphs (north)
    fill(5, 3, 18, 11, T_FLOOR)
    rect_wall(5, 3, 18, 11)
    m[11][7] = T_DOOR
    m[11][8] = T_DOOR
    m[6][11] = T_EXIT  # boss room marker / portal after win
    m[6][12] = T_EXIT

    # East wing hint (locked feel — walls only stub)
    fill(20, 14, 28, 20, T_FLOOR2)
    rect_wall(20, 14, 28, 20)
    # no door yet — future domain

    # Pond
    fill(14, 20, 18, 24, T_WATER)

    return m


SOLID = {T_WALL, T_WATER, T_VOID}


@dataclass
class NPC:
    x: float
    y: float
    name: str
    color: tuple
    lines: list[str]
    glyph: str = "◈"


@dataclass
class EncounterSpot:
    x: int
    y: int
    name: str
    active: bool = True


@dataclass
class Player:
    x: float = 7.5
    y: float = 23.5
    speed: float = 3.6
    facing: tuple = (0, 1)
    hp: int = 40
    max_hp: int = 40
    insight: int = 8
    will: int = 6
    luck: int = 4


@dataclass
class Companion:
    x: float = 7.5
    y: float = 24.5
    name: str = "Sol"
    line: str = "The light grows. I walk with you."


@dataclass
class BattleState:
    foe_name: str = "The Overclaimer"
    foe_hp: int = 30
    foe_max: int = 30
    foe_shield: int = 20  # false HP — MEASURE strips it
    measured: bool = False
    log: list[str] = field(default_factory=list)
    player_cd: dict = field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0})
    turn: str = "player"  # player | foe
    done: bool = False
    won: bool = False


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("The Long Light — School World")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("dejavusansmono", 14)
        self.font_sm = pygame.font.SysFont("dejavusansmono", 12)
        self.font_lg = pygame.font.SysFont("dejavusans", 22, bold=True)
        self.font_title = pygame.font.SysFont("dejavusans", 28, bold=True)

        self.world = build_world()
        self.player = Player()
        self.companion = Companion()
        self.mode = Mode.TITLE
        self.keys = pygame.key.get_pressed()
        self.dialogue: list[str] = []
        self.dialogue_i = 0
        self.dialogue_speaker = ""
        self.battle: Optional[BattleState] = None
        self.msg = ""
        self.msg_t = 0.0
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.boss_defeated = False
        self.steps = 0

        self.npcs = [
            NPC(9.5, 21.5, "Magister Ember", C_FLAME, [
                "Seeker. The Sanctum holds the first fire.",
                "North lies the Hall of Glyphs. Walk the path.",
                "When the Overclaimer appears — MEASURE first. Never strike the false shield.",
            ], "🔥"),
            NPC(10.5, 7.5, "Cipher", C_VIOLET, [
                "◈ The Hall records what you can hold.",
                "Broken ideas wander here. They grow fat on unmeasured claims.",
                "Your skills: 1 MEASURE · 2 COMPRESS · 3 TRANSMUTE · 4 BREAK",
            ], "⟁"),
        ]
        self.encounters = [
            EncounterSpot(8, 14, "The Overclaimer"),
            EncounterSpot(12, 8, "The Overclaimer"),
        ]

    # ── Helpers ──────────────────────────────────────────────────────────────
    def toast(self, text: str, t: float = 2.2):
        self.msg = text
        self.msg_t = t

    def solid_at(self, tx: int, ty: int) -> bool:
        if tx < 0 or ty < 0 or tx >= MAP_W or ty >= MAP_H:
            return True
        return self.world[ty][tx] in SOLID

    def try_move(self, dx: float, dy: float, dt: float):
        p = self.player
        nx = p.x + dx * p.speed * dt
        ny = p.y + dy * p.speed * dt
        # collision as circle radius ~0.3 tiles against tile centers
        r = 0.28
        for ax, ay in ((nx, p.y), (p.x, ny), (nx, ny)):
            ok = True
            for ox, oy in ((-r, -r), (r, -r), (-r, r), (r, r)):
                if self.solid_at(int(ax + ox), int(ay + oy)):
                    ok = False
                    break
            if ax == nx and ay == p.y and ok:
                p.x = nx
            if ax == p.x and ay == ny and ok:
                p.y = ny
            if ax == nx and ay == ny and ok:
                p.x, p.y = nx, ny
        if dx or dy:
            if abs(dx) > abs(dy):
                p.facing = (1 if dx > 0 else -1, 0)
            else:
                p.facing = (0, 1 if dy > 0 else -1)
            self.steps += 1
            # companion lag follow
            c = self.companion
            tx, ty = p.x - p.facing[0] * 0.7, p.y - p.facing[1] * 0.7
            c.x += (tx - c.x) * min(1.0, 6 * dt)
            c.y += (ty - c.y) * min(1.0, 6 * dt)

    def tile_under(self) -> int:
        return self.world[int(self.player.y)][int(self.player.x)]

    def start_dialogue(self, speaker: str, lines: list[str]):
        self.dialogue = lines[:]
        self.dialogue_i = 0
        self.dialogue_speaker = speaker
        self.mode = Mode.DIALOGUE

    def interact(self):
        p = self.player
        # NPC in front
        fx = p.x + p.facing[0] * 0.9
        fy = p.y + p.facing[1] * 0.9
        for npc in self.npcs:
            if (npc.x - fx) ** 2 + (npc.y - fy) ** 2 < 1.1:
                self.start_dialogue(npc.name, npc.lines)
                return
        # Shrine under / adjacent
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                tx, ty = int(p.x) + dx, int(p.y) + dy
                if 0 <= tx < MAP_W and 0 <= ty < MAP_H and self.world[ty][tx] == T_SHRINE:
                    p.hp = p.max_hp
                    self.toast("Shrine — Will restored. Rest is rest. Nothing wilts.")
                    self.companion.line = "I am still here. The fire stays lit."
                    return
                if 0 <= tx < MAP_W and 0 <= ty < MAP_H and self.world[ty][tx] == T_EXIT:
                    if self.boss_defeated:
                        self.mode = Mode.WIN
                    else:
                        self.toast("The portal hums — defeat the Overclaimer first.")
                    return
        self.toast("… nothing to touch.")

    def check_encounter(self):
        if self.boss_defeated:
            return
        px, py = int(self.player.x), int(self.player.y)
        for e in self.encounters:
            if e.active and e.x == px and e.y == py:
                e.active = False
                self.begin_battle(e.name)
                return
        # chance in Hall floors after steps
        if self.world[py][px] == T_FLOOR and 3 <= py <= 11 and self.steps % 47 == 0:
            self.begin_battle("The Overclaimer")

    def begin_battle(self, name: str):
        self.battle = BattleState(foe_name=name)
        self.battle.log = [f"{name} swells with unmeasured claims!", "Press 1 to MEASURE."]
        self.mode = Mode.BATTLE
        self.toast(f"Battle — {name}")

    # ── Combat ───────────────────────────────────────────────────────────────
    def battle_skill(self, n: int):
        b = self.battle
        if not b or b.done or b.turn != "player":
            return
        if b.player_cd.get(n, 0) > 0:
            b.log.append("Skill cooling…")
            return
        p = self.player
        if n == 1:  # MEASURE
            b.measured = True
            stripped = b.foe_shield
            b.foe_shield = 0
            b.player_cd[1] = 2
            b.log.append(f"MEASURE (Π) — false shield ({stripped}) collapses.")
            b.log.append(f"True form: {b.foe_hp} HP.")
        elif n == 2:  # COMPRESS
            dmg = p.insight + (6 if b.measured else 2)
            b.foe_hp = max(0, b.foe_hp - dmg)
            b.player_cd[2] = 1
            b.log.append(f"COMPRESS (⟁) — {dmg} damage." + ("" if b.measured else " (weak — not measured)"))
        elif n == 3:  # TRANSMUTE
            heal = p.will + 2
            p.hp = min(p.max_hp, p.hp + heal)
            b.player_cd[3] = 3
            b.log.append(f"TRANSMUTE — restore {heal} Will.")
        elif n == 4:  # BREAK
            dmg = p.luck + 3
            b.foe_hp = max(0, b.foe_hp - dmg)
            b.player_cd[4] = 2
            b.log.append(f"BREAK — snap a loop for {dmg}.")
        else:
            return

        if b.foe_hp <= 0:
            b.done = True
            b.won = True
            b.log.append(f"{b.foe_name} dissolves into a glyph shard.")
            self.boss_defeated = True
            self.companion.line = "Well measured. The Hall remembers you."
            return

        b.turn = "foe"
        self.foe_act()

    def foe_act(self):
        b = self.battle
        if not b or b.done:
            return
        p = self.player
        # If still shielded, brag; else hit
        if b.foe_shield > 0:
            b.foe_shield = min(30, b.foe_shield + 3)
            dmg = 3
            p.hp = max(0, p.hp - dmg)
            b.log.append(f"{b.foe_name} inflates further! You take {dmg}.")
        else:
            dmg = random.randint(4, 7)
            p.hp = max(0, p.hp - dmg)
            b.log.append(f"{b.foe_name} lashes with hollow certainty — {dmg} damage.")
        # tick CDs
        for k in b.player_cd:
            b.player_cd[k] = max(0, b.player_cd[k] - 1)
        if p.hp <= 0:
            b.done = True
            b.won = False
            b.log.append("You fall. The shrine will take you back.")
            p.hp = p.max_hp
            p.x, p.y = 7.5, 22.5
            # reactivate one encounter
            for e in self.encounters:
                e.active = True
            return
        b.turn = "player"

    def end_battle(self):
        self.mode = Mode.OVERWORLD
        self.battle = None
        if self.boss_defeated:
            self.toast("Overclaimer down. Seek the portal in the Hall (north).")

    # ── Update ───────────────────────────────────────────────────────────────
    def update(self, dt: float):
        if self.msg_t > 0:
            self.msg_t -= dt
        self.keys = pygame.key.get_pressed()

        if self.mode == Mode.OVERWORLD:
            dx = dy = 0.0
            if self.keys[pygame.K_a] or self.keys[pygame.K_LEFT]:
                dx -= 1
            if self.keys[pygame.K_d] or self.keys[pygame.K_RIGHT]:
                dx += 1
            if self.keys[pygame.K_w] or self.keys[pygame.K_UP]:
                dy -= 1
            if self.keys[pygame.K_s] or self.keys[pygame.K_DOWN]:
                dy += 1
            if dx or dy:
                # normalize diagonal
                l = math.hypot(dx, dy) or 1
                self.try_move(dx / l, dy / l, dt)
                self.check_encounter()
            # camera
            self.cam_x = max(0, min(MAP_W - VIEW_W, self.player.x - VIEW_W / 2))
            self.cam_y = max(0, min(MAP_H - VIEW_H, self.player.y - VIEW_H / 2))

    # ── Draw ─────────────────────────────────────────────────────────────────
    def tile_color(self, t: int, x: int, y: int) -> tuple:
        if t == T_FLOOR:
            return C_FLOOR if (x + y) % 2 == 0 else C_FLOOR2
        if t == T_FLOOR2:
            return C_FLOOR2
        if t == T_WALL:
            return C_WALL
        if t == T_GRASS:
            return C_GRASS if (x * 3 + y) % 5 else (30, 44, 36)
        if t == T_PATH:
            return C_PATH
        if t == T_DOOR:
            return C_DOOR
        if t == T_SHRINE:
            return (60, 50, 30)
        if t == T_EXIT:
            return (40, 30, 70)
        if t == T_WATER:
            return C_WATER
        return C_VOID

    def draw_overworld(self):
        sx = self.cam_x
        sy = self.cam_y
        for ty in range(VIEW_H + 1):
            for tx in range(VIEW_W + 1):
                wx, wy = int(sx) + tx, int(sy) + ty
                if 0 <= wx < MAP_W and 0 <= wy < MAP_H:
                    t = self.world[wy][wx]
                    col = self.tile_color(t, wx, wy)
                else:
                    col = C_VOID
                px = int((tx - (sx % 1)) * TILE)
                py = int((ty - (sy % 1)) * TILE)
                pygame.draw.rect(self.screen, col, (px, py, TILE, TILE))
                if 0 <= wx < MAP_W and 0 <= wy < MAP_H:
                    t = self.world[wy][wx]
                    if t == T_WALL:
                        pygame.draw.rect(self.screen, C_WALL_EDGE, (px, py, TILE, 3))
                    if t == T_SHRINE:
                        pygame.draw.circle(self.screen, C_GOLD, (px + TILE // 2, py + TILE // 2), 8)
                        pygame.draw.circle(self.screen, C_FLAME, (px + TILE // 2, py + TILE // 2 - 4), 3)
                    if t == T_EXIT:
                        pygame.draw.rect(self.screen, C_VIOLET, (px + 6, py + 6, TILE - 12, TILE - 12), 2)
                    if t == T_DOOR:
                        pygame.draw.rect(self.screen, (120, 90, 50), (px + 4, py + 8, TILE - 8, TILE - 8))

        # encounter glints
        for e in self.encounters:
            if not e.active:
                continue
            ex = int((e.x + 0.5 - sx) * TILE)
            ey = int((e.y + 0.5 - sy) * TILE)
            pygame.draw.circle(self.screen, C_RED, (ex, ey), 5)
            pygame.draw.circle(self.screen, C_GOLD, (ex, ey), 8, 1)

        # NPCs
        for npc in self.npcs:
            nx = int((npc.x - sx) * TILE)
            ny = int((npc.y - sy) * TILE)
            pygame.draw.rect(self.screen, npc.color, (nx - 10, ny - 14, 20, 24), border_radius=4)
            pygame.draw.circle(self.screen, C_TEXT, (nx, ny - 18), 3)

        # companion
        c = self.companion
        cx = int((c.x - sx) * TILE)
        cy = int((c.y - sy) * TILE)
        pygame.draw.circle(self.screen, C_CYAN, (cx, cy), 9)
        pygame.draw.circle(self.screen, C_GOLD, (cx, cy), 9, 1)

        # player
        p = self.player
        px = int((p.x - sx) * TILE)
        py = int((p.y - sy) * TILE)
        pygame.draw.rect(self.screen, C_GOLD, (px - 11, py - 14, 22, 26), border_radius=5)
        # face marker
        fx, fy = p.facing
        pygame.draw.circle(self.screen, C_VOID, (px + fx * 6, py + fy * 6 - 2), 3)

        # HUD
        pygame.draw.rect(self.screen, C_PANEL, (0, 0, W, 28))
        hud = f"WILL {p.hp}/{p.max_hp}   Hall of Glyphs   E:talk   ESC:pause"
        self.screen.blit(self.font_sm.render(hud, True, C_TEXT), (8, 7))
        # companion line
        pygame.draw.rect(self.screen, C_PANEL, (0, H - 36, W, 36))
        self.screen.blit(self.font_sm.render(f"⊚ {c.name}: {c.line}", True, C_CYAN), (8, H - 26))

    def draw_dialogue(self):
        self.draw_overworld()
        box_h = 110
        pygame.draw.rect(self.screen, C_PANEL, (16, H - box_h - 16, W - 32, box_h), border_radius=8)
        pygame.draw.rect(self.screen, C_GOLD, (16, H - box_h - 16, W - 32, box_h), 1, border_radius=8)
        name = self.font.render(self.dialogue_speaker, True, C_GOLD)
        self.screen.blit(name, (28, H - box_h - 6))
        if self.dialogue_i < len(self.dialogue):
            line = self.dialogue[self.dialogue_i]
            # wrap simple
            words = line.split()
            rows, cur = [], ""
            for w in words:
                test = (cur + " " + w).strip()
                if self.font.size(test)[0] > W - 64:
                    rows.append(cur)
                    cur = w
                else:
                    cur = test
            if cur:
                rows.append(cur)
            for i, r in enumerate(rows[:4]):
                self.screen.blit(self.font.render(r, True, C_TEXT), (28, H - box_h + 22 + i * 18))
        hint = self.font_sm.render("E / Enter — next", True, C_DIM)
        self.screen.blit(hint, (W - 140, H - 28))

    def draw_battle(self):
        self.screen.fill(C_VOID)
        b = self.battle
        assert b
        # title
        self.screen.blit(self.font_lg.render("INNER DEMON", True, C_RED), (20, 16))
        self.screen.blit(self.font.render(b.foe_name, True, C_GOLD), (20, 48))
        # foe body
        cx, cy = W // 2, 130
        pygame.draw.circle(self.screen, (80, 30, 40), (cx, cy), 50)
        pygame.draw.circle(self.screen, C_RED, (cx, cy), 50, 2)
        if b.foe_shield > 0:
            pygame.draw.circle(self.screen, C_VIOLET, (cx, cy), 62, 3)
            self.screen.blit(self.font_sm.render(f"FALSE SHIELD {b.foe_shield}", True, C_VIOLET), (cx - 55, cy + 60))
        # HP bars
        def bar(x, y, w, h, frac, col):
            pygame.draw.rect(self.screen, (40, 40, 50), (x, y, w, h))
            pygame.draw.rect(self.screen, col, (x, y, int(w * max(0, min(1, frac))), h))
            pygame.draw.rect(self.screen, C_DIM, (x, y, w, h), 1)

        bar(20, 200, W - 40, 12, b.foe_hp / b.foe_max, C_RED)
        self.screen.blit(self.font_sm.render(f"True HP {b.foe_hp}/{b.foe_max}" + ("  [MEASURED]" if b.measured else ""), True, C_TEXT), (20, 216))
        bar(20, 240, W - 40, 12, self.player.hp / self.player.max_hp, C_GREEN)
        self.screen.blit(self.font_sm.render(f"Your Will {self.player.hp}/{self.player.max_hp}", True, C_TEXT), (20, 256))

        # skills
        skills = [
            (1, "MEASURE", "strip false shield", C_CYAN),
            (2, "COMPRESS", "damage (best if measured)", C_VIOLET),
            (3, "TRANSMUTE", "heal Will", C_GREEN),
            (4, "BREAK", "burst damage", C_FLAME),
        ]
        y0 = 290
        for i, (n, name, desc, col) in enumerate(skills):
            cd = b.player_cd.get(n, 0)
            label = f"[{n}] {name}" + (f"  CD{cd}" if cd else "")
            self.screen.blit(self.font.render(label, True, col if cd == 0 else C_DIM), (24, y0 + i * 28))
            self.screen.blit(self.font_sm.render(desc, True, C_DIM), (200, y0 + i * 28 + 2))

        # log
        pygame.draw.rect(self.screen, C_PANEL, (16, H - 130, W - 32, 114), border_radius=6)
        for i, line in enumerate(b.log[-5:]):
            self.screen.blit(self.font_sm.render(line[:70], True, C_TEXT), (28, H - 120 + i * 18))

        if b.done:
            end = "VICTORY — Enter to continue" if b.won else "DEFEATED — Enter to rise at Sanctum"
            self.screen.blit(self.font.render(end, True, C_GOLD if b.won else C_RED), (20, H - 28))

    def draw_title(self):
        self.screen.fill(C_VOID)
        title = self.font_title.render("THE LONG LIGHT", True, C_GOLD)
        sub = self.font.render("School World  ·  v0.1", True, C_CYAN)
        tag = self.font_sm.render("Lycheetah Mystery School  ·  walk · talk · measure", True, C_DIM)
        self.screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 80))
        self.screen.blit(sub, (W // 2 - sub.get_width() // 2, H // 2 - 40))
        self.screen.blit(tag, (W // 2 - tag.get_width() // 2, H // 2 - 12))
        lines = [
            "Enter — begin",
            "WASD walk · E talk · 1–4 battle skills",
            "Defeat the Overclaimer. Find the portal.",
            "Companion never guilts your absence.",
        ]
        for i, L in enumerate(lines):
            s = self.font_sm.render(L, True, C_TEXT if i == 0 else C_DIM)
            self.screen.blit(s, (W // 2 - s.get_width() // 2, H // 2 + 30 + i * 20))

    def draw_pause(self):
        self.draw_overworld()
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        t = self.font_lg.render("PAUSED", True, C_GOLD)
        self.screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 20))
        s = self.font_sm.render("ESC — resume", True, C_DIM)
        self.screen.blit(s, (W // 2 - s.get_width() // 2, H // 2 + 16))

    def draw_win(self):
        self.screen.fill(C_VOID)
        t = self.font_title.render("THE WORK BEGINS", True, C_GOLD)
        self.screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 60))
        lines = [
            "You measured what was false.",
            "The Hall of Glyphs opens deeper floors next.",
            "v0.1 complete — School World lives.",
            "",
            "Enter / ESC — return to title",
        ]
        for i, L in enumerate(lines):
            s = self.font.render(L, True, C_TEXT if L else C_DIM)
            self.screen.blit(s, (W // 2 - s.get_width() // 2, H // 2 - 10 + i * 24))

    def draw_toast(self):
        if self.msg_t <= 0 or not self.msg:
            return
        s = self.font_sm.render(self.msg, True, C_GOLD)
        pad = 10
        r = s.get_rect()
        box = pygame.Rect(W // 2 - r.w // 2 - pad, 40, r.w + pad * 2, r.h + pad)
        pygame.draw.rect(self.screen, C_PANEL, box, border_radius=6)
        pygame.draw.rect(self.screen, C_GOLD, box, 1, border_radius=6)
        self.screen.blit(s, (box.x + pad, box.y + pad // 2))

    # ── Events ───────────────────────────────────────────────────────────────
    def on_key(self, key: int):
        if self.mode == Mode.TITLE:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.mode = Mode.OVERWORLD
                self.toast("Sanctum. Walk north to the Hall.")
            return

        if self.mode == Mode.PAUSE:
            if key == pygame.K_ESCAPE:
                self.mode = Mode.OVERWORLD
            return

        if self.mode == Mode.WIN:
            if key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_e):
                self.mode = Mode.TITLE
            return

        if self.mode == Mode.DIALOGUE:
            if key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                self.dialogue_i += 1
                if self.dialogue_i >= len(self.dialogue):
                    self.mode = Mode.OVERWORLD
            return

        if self.mode == Mode.BATTLE:
            b = self.battle
            if b and b.done:
                if key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
                    self.end_battle()
                return
            if key == pygame.K_1:
                self.battle_skill(1)
            elif key == pygame.K_2:
                self.battle_skill(2)
            elif key == pygame.K_3:
                self.battle_skill(3)
            elif key == pygame.K_4:
                self.battle_skill(4)
            elif key == pygame.K_ESCAPE:
                # no flee cheese on boss first pass — soft flee
                self.toast("No fleeing the lesson — fight or fall.")
            return

        if self.mode == Mode.OVERWORLD:
            if key == pygame.K_e:
                self.interact()
            elif key == pygame.K_ESCAPE:
                self.mode = Mode.PAUSE

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    self.on_key(ev.key)

            self.update(dt)

            if self.mode == Mode.TITLE:
                self.draw_title()
            elif self.mode == Mode.OVERWORLD:
                self.draw_overworld()
            elif self.mode == Mode.DIALOGUE:
                self.draw_dialogue()
            elif self.mode == Mode.BATTLE:
                self.draw_battle()
            elif self.mode == Mode.PAUSE:
                self.draw_pause()
            elif self.mode == Mode.WIN:
                self.draw_win()

            self.draw_toast()
            pygame.display.flip()

        pygame.quit()


def main():
    try:
        Game().run()
    except pygame.error as e:
        print("Pygame display error:", e, file=sys.stderr)
        print("Need a graphical session (display). On headless SSH this won't open a window.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
