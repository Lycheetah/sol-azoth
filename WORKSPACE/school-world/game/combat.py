"""Turn-ish skill combat — framework moves as D&D-flavored actions."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from .content import FOES, SKILLS


@dataclass
class Battle:
    foe_id: str
    foe_name: str
    foe_hp: int
    foe_max: int
    foe_shield: int
    foe_atk: int
    foe_def: int
    kind: str
    xp: int
    loot: list
    color: tuple
    measured: bool = False
    phased: bool = False  # riddle wraith
    log: list = field(default_factory=list)
    cd: dict = field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0})
    turn: str = "player"
    done: bool = False
    won: bool = False
    flag_on_win: Optional[str] = None
    boss: bool = False
    line_i: int = 0
    lines: list = field(default_factory=list)

    @classmethod
    def from_foe(cls, foe_id: str, flag_on_win=None, boss=False) -> "Battle":
        f = FOES[foe_id]
        return cls(
            foe_id=foe_id,
            foe_name=f["name"],
            foe_hp=f["hp"],
            foe_max=f["hp"],
            foe_shield=f.get("shield", 0),
            foe_atk=f["atk"],
            foe_def=f["def"],
            kind=f["kind"],
            xp=f["xp"],
            loot=list(f.get("loot", [])),
            color=f["color"],
            lines=list(f.get("lines", [])),
            flag_on_win=flag_on_win,
            boss=boss or f["kind"] == "boss",
            log=[f"{f['name']} emerges!", "1 MEASURE · 2 COMPRESS · 3 TRANSMUTE · 4 BREAK · 5 STRIKE"],
        )


def _dmg(base: int, insight: int, defense: int, mult: float = 1.0) -> int:
    raw = (base + insight) * mult - defense * 0.5
    return max(1, int(raw + random.randint(0, 2)))


def player_skill(battle: Battle, n: int, stats: dict) -> list[str]:
    """Apply skill. stats: hp, max_hp, insight, will, luck, bonus, relics."""
    if battle.done or battle.turn != "player":
        return []
    if battle.cd.get(n, 0) > 0:
        return ["Skill on cooldown."]
    if n not in SKILLS:
        return ["Unknown skill."]

    logs = []
    insight = stats["insight"] + stats.get("bonus_insight", 0)
    will = stats["will"]
    luck = stats["luck"]
    bonus = stats.get("bonus", "")
    has_lens = "lens" in stats.get("relics", [])

    # Phase: wraith intangible until measured once this fight or random
    if battle.kind == "phase" and battle.phased and n not in (1, 4):
        battle.phased = False
        logs.append("Your strike passes through mist!")
        battle.turn = "foe"
        return logs

    if n == 1:  # MEASURE
        battle.measured = True
        stripped = battle.foe_shield
        battle.foe_shield = 0
        battle.cd[1] = 1 if bonus == "measure_boost" else 2
        logs.append(f"Π MEASURE — false shield ({stripped}) collapses.")
        logs.append(f"True form revealed: {battle.foe_hp} HP.")
        if has_lens:
            extra = 4
            battle.foe_hp = max(0, battle.foe_hp - extra)
            logs.append(f"Lens of Clarity burns {extra} true damage.")
        if battle.kind == "phase":
            battle.phased = False
            logs.append("The Wraith solidifies under measure.")
    elif n == 2:  # COMPRESS
        mult = 1.6 if battle.measured else 0.7
        if battle.kind == "phase" and battle.measured:
            mult += 0.3
        dmg = _dmg(6, insight, battle.foe_def, mult)
        battle.foe_hp = max(0, battle.foe_hp - dmg)
        battle.cd[2] = 1
        note = " (measured!)" if battle.measured else " (unmeasured — weak)"
        logs.append(f"⟁ COMPRESS — {dmg} damage{note}.")
    elif n == 3:  # TRANSMUTE
        heal = will + 4 + (4 if bonus == "transmute_boost" else 0)
        if battle.kind == "residue":
            heal += 3
            dmg = _dmg(4, insight, battle.foe_def, 1.0)
            battle.foe_hp = max(0, battle.foe_hp - dmg)
            logs.append(f"☿ TRANSMUTE completes the Half-Made — {dmg} + heal {heal}.")
        else:
            logs.append(f"☿ TRANSMUTE — restore {heal} Will.")
        stats["hp"] = min(stats["max_hp"], stats["hp"] + heal)
        battle.cd[3] = 2 if bonus == "transmute_boost" else 3
    elif n == 4:  # BREAK
        mult = 1.8 if battle.kind == "loop" else 1.1
        dmg = _dmg(5, luck + insight // 2, battle.foe_def, mult)
        battle.foe_hp = max(0, battle.foe_hp - dmg)
        battle.cd[4] = 2
        logs.append(f"∴ BREAK — {dmg} damage" + (" (loop snapped!)" if battle.kind == "loop" else "."))
        if battle.kind == "phase":
            battle.phased = False
    elif n == 5:  # STRIKE
        mult = 1.0
        if battle.kind == "loop":
            # loop feeds on basic
            battle.foe_hp = min(battle.foe_max, battle.foe_hp + 4)
            logs.append("⟡ STRIKE — The Loop feeds and heals 4! Use BREAK.")
        else:
            dmg = _dmg(3, insight // 2, battle.foe_def, mult)
            if battle.foe_shield > 0:
                battle.foe_shield = max(0, battle.foe_shield - dmg)
                logs.append(f"⟡ STRIKE chips false shield ({dmg}). MEASURE it!")
            else:
                battle.foe_hp = max(0, battle.foe_hp - dmg)
                logs.append(f"⟡ STRIKE — {dmg} damage.")
        battle.cd[5] = 0

    if battle.foe_hp <= 0 and battle.foe_shield <= 0:
        battle.done = True
        battle.won = True
        logs.append(f"{battle.foe_name} dissolves into light.")
        return logs

    battle.turn = "foe"
    return logs


def foe_act(battle: Battle, stats: dict) -> list[str]:
    if battle.done:
        return []
    logs = []
    # tick player CDs
    for k in battle.cd:
        battle.cd[k] = max(0, battle.cd[k] - 1)

    # taunt
    if battle.lines and random.random() < 0.4:
        logs.append(f'"{battle.lines[battle.line_i % len(battle.lines)]}"')
        battle.line_i += 1

    if battle.kind == "phase" and random.random() < 0.45:
        battle.phased = True
        logs.append(f"{battle.foe_name} phases into riddle-mist!")

    if battle.foe_shield > 0 and battle.kind in ("overclaim", "boss"):
        battle.foe_shield = min(40, battle.foe_shield + 2)
        dmg = max(2, battle.foe_atk - stats.get("will", 0) // 4)
        if stats.get("bonus") == "guard":
            dmg = max(1, dmg - 2)
        stats["hp"] = max(0, stats["hp"] - dmg)
        logs.append(f"{battle.foe_name} inflates! You take {dmg}.")
    elif battle.kind == "loop" and random.random() < 0.3:
        battle.foe_hp = min(battle.foe_max, battle.foe_hp + 5)
        logs.append(f"{battle.foe_name} cycles and heals 5.")
        dmg = max(2, battle.foe_atk - 1)
        stats["hp"] = max(0, stats["hp"] - dmg)
        logs.append(f"Then strikes for {dmg}.")
    else:
        dmg = max(2, battle.foe_atk + random.randint(0, 3) - stats.get("will", 0) // 5)
        if stats.get("bonus") == "guard":
            dmg = max(1, dmg - 2)
        stats["hp"] = max(0, stats["hp"] - dmg)
        logs.append(f"{battle.foe_name} hits for {dmg}.")

    if stats["hp"] <= 0:
        battle.done = True
        battle.won = False
        logs.append("You fall. The Sanctum shrine will take you.")
    else:
        battle.turn = "player"
    return logs
