"""Đọc puzzle JSON. Định dạng: xem docs/puzzle_format.md"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

from .models import Character, Clue, ClueType, Region, RegionKind, Status


@dataclass
class Puzzle:
    name: str
    size: int
    characters: list[Character]          # sắp xếp theo tên
    solution: dict[str, Status]          # HIDDEN - chỉ GameEngine được giữ
    clues: dict[str, Clue]               # cell -> clue (HIDDEN tới khi lật)
    initial_revealed: list[str]          # các cell face-up ban đầu


def _region(d: dict | None) -> Region | None:
    if d is None:
        return None
    return Region(RegionKind(d["kind"]), d.get("ref"), tuple(d.get("cells", [])))


def _clue(cid: str, d: dict) -> Clue:
    return Clue(
        id=cid,
        type=ClueType(d["type"]),
        targets=tuple(d.get("targets", [])),
        fact_status=Status(d["status"]) if "status" in d else None,
        region=_region(d.get("region")),
        k=d.get("k"),
        extra=d.get("extra", {}),
    )


def load_puzzle(path: str | Path) -> Puzzle:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    chars = sorted(
        (Character(c["cell"], c["name"], c["profession"]) for c in data["characters"]),
        key=lambda c: c.name,
    )
    solution = {c["cell"]: Status(c["status"]) for c in data["characters"]}
    clues = {c["cell"]: _clue(f"clue_{c['cell']}", c["clue"]) for c in data["characters"]}
    return Puzzle(data["name"], data["size"], chars, solution, clues, data["initial_revealed"])
