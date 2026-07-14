"""Display, palette, tiles, modes."""
from enum import Enum, auto

TILE = 32
VIEW_W, VIEW_H = 22, 16
W, H = VIEW_W * TILE, VIEW_H * TILE
FPS = 60

# Lycheetah palette
C_VOID = (8, 6, 14)
C_FLOOR = (30, 26, 50)
C_FLOOR2 = (38, 32, 60)
C_WALL = (16, 12, 28)
C_WALL_HI = (48, 40, 78)
C_GOLD = (240, 208, 128)
C_CYAN = (0, 212, 255)
C_VIOLET = (155, 89, 182)
C_GREEN = (46, 204, 113)
C_RED = (231, 76, 60)
C_TEXT = (230, 222, 245)
C_DIM = (130, 120, 160)
C_PANEL = (14, 10, 24)
C_PANEL2 = (22, 16, 36)
C_FLAME = (255, 107, 53)
C_GRASS = (28, 48, 38)
C_GRASS2 = (34, 56, 44)
C_PATH = (52, 44, 68)
C_DOOR = (100, 78, 42)
C_WATER = (18, 42, 88)
C_SAND = (70, 60, 48)
C_TREE = (20, 40, 28)
C_RUG = (60, 30, 50)
C_ALTAR = (90, 75, 40)
C_WHITE = (255, 248, 231)

# Tiles
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
T_TREE = 10
T_SAND = 11
T_RUG = 12
T_ALTAR = 13
T_WARP = 14  # area transition
T_TALL = 15  # tall grass — wild encounter chance

SOLID = {T_WALL, T_WATER, T_VOID, T_TREE}

SAVE_PATH = "savegame.json"


class Mode(Enum):
    TITLE = auto()
    ARCHETYPE = auto()
    OVERWORLD = auto()
    DIALOGUE = auto()
    BATTLE = auto()
    MENU = auto()
    PARTY = auto()
    INVENTORY = auto()
    CODEX = auto()
    QUEST = auto()
    PAUSE = auto()
    WIN = auto()
    GAMEOVER = auto()
