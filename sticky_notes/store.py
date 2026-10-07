"""Persist sticky notes to AppData as JSON."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def _app_data_dir() -> Path:
    root = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    path = Path(root) / "StickyNotes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def notes_file() -> Path:
    return _app_data_dir() / "notes.json"


@dataclass
class Note:
    id: str
    text: str = ""
    color: str = "yellow"
    x: int = 120
    y: int = 120
    width: int = 280
    height: int = 280
    always_on_top: bool = False

    @staticmethod
    def create(*, x: int = 120, y: int = 120, color: str = "yellow") -> Note:
        return Note(id=str(uuid.uuid4()), x=x, y=y, color=color)


def load_notes() -> list[Note]:
    path = notes_file()
    if not path.exists():
        return []
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    notes: list[Note] = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict) or "id" not in item:
            continue
        notes.append(
            Note(
                id=str(item["id"]),
                text=str(item.get("text", "")),
                color=str(item.get("color", "yellow")),
                x=int(item.get("x", 120)),
                y=int(item.get("y", 120)),
                width=int(item.get("width", 280)),
                height=int(item.get("height", 280)),
                always_on_top=bool(item.get("always_on_top", False)),
            )
        )
    return notes


def save_notes(notes: list[Note]) -> None:
    payload = [asdict(note) for note in notes]
    path = notes_file()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
