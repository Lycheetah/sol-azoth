"""Save / load school world."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import SAVE_PATH


def save_path(base: Path) -> Path:
    return base / SAVE_PATH


def write_save(base: Path, data: dict[str, Any]) -> None:
    p = save_path(base)
    p.write_text(json.dumps(data, indent=2))


def read_save(base: Path) -> dict[str, Any] | None:
    p = save_path(base)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def delete_save(base: Path) -> None:
    p = save_path(base)
    if p.exists():
        p.unlink()
