"""Đọc puzzle JSON. Định dạng: xem docs/puzzle_format.md

load_puzzle(path) -> Puzzle. File sai định dạng -> PuzzleError (thông báo tiếng
Việt, nói rõ sai ở đâu) thay vì KeyError/TypeError khó hiểu.

Lưu ý: ở đây chỉ kiểm tra CẤU TRÚC file. Việc "đáp án có thỏa mọi clue không" và
"nghiệm có duy nhất không" cần evaluator (Phần 2) và uniqueness check (Phần 4).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import grid
from .models import Character, Clue, ClueType, Region, RegionKind, Status


class PuzzleError(ValueError):
    """File puzzle không hợp lệ."""


@dataclass
class Puzzle:
    name: str
    size: int
    characters: list[Character]          # sắp xếp theo tên
    solution: dict[str, Status]          # HIDDEN - chỉ GameEngine được giữ
    clues: dict[str, Clue]               # cell -> clue (HIDDEN tới khi lật)
    initial_revealed: list[str]          # các cell face-up ban đầu


_COUNTING = {ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST}


def _region(d: dict | None) -> Region | None:
    if d is None:
        return None
    if not isinstance(d, dict) or "kind" not in d:
        raise PuzzleError(f"region phải là object có 'kind': {d!r}")
    try:
        kind = RegionKind(d["kind"])
    except ValueError:
        raise PuzzleError(f"region.kind không hợp lệ: {d['kind']!r} "
                          f"(chỉ nhận {[k.value for k in RegionKind]})") from None
    return Region(kind, d.get("ref"), tuple(d.get("cells", [])))


def _clue(cid: str, d: dict) -> Clue:
    if not isinstance(d, dict) or "type" not in d:
        raise PuzzleError("clue phải là object có 'type'")
    try:
        ctype = ClueType(d["type"])
    except ValueError:
        raise PuzzleError(f"clue.type không hợp lệ: {d['type']!r}") from None
    try:
        fact_status = Status(d["status"]) if "status" in d else None
    except ValueError:
        raise PuzzleError(f"clue.status phải là CRIMINAL/INNOCENT, không phải {d['status']!r}") from None
    return Clue(
        id=cid,
        type=ctype,
        targets=tuple(d.get("targets", [])),
        fact_status=fact_status,
        region=_region(d.get("region")),
        k=d.get("k"),
        extra=d.get("extra", {}),
    )


def _check_clue(clue: Clue, size: int) -> None:
    """Kiểm tra tham số của 1 clue (chỉ phần cấu trúc)."""
    for t in clue.targets:
        if not grid.in_grid(t, size):
            raise PuzzleError(f"targets có ô không tồn tại: {t!r}")
    if clue.type == ClueType.FACT:
        if len(clue.targets) != 1 or clue.fact_status is None:
            raise PuzzleError("FACT cần đúng 1 ô trong 'targets' và có 'status'")
    elif clue.type in (ClueType.SAME, ClueType.DIFFERENT):
        if len(clue.targets) != 2 or clue.targets[0] == clue.targets[1]:
            raise PuzzleError(f"{clue.type.value} cần đúng 2 ô KHÁC NHAU trong 'targets'")
    elif clue.type in _COUNTING:
        if clue.region is None:
            raise PuzzleError(f"{clue.type.value} cần có 'region'")
        try:
            n = len(grid.region_cells(clue.region, size))
        except ValueError as e:
            raise PuzzleError(str(e)) from None
        # bool là con của int trong Python -> loại riêng
        if not isinstance(clue.k, int) or isinstance(clue.k, bool) or not 0 <= clue.k <= n:
            raise PuzzleError(f"{clue.type.value}: k phải là số nguyên trong [0, {n}], đang là {clue.k!r}")
    else:
        # Clue mở rộng (PARITY, COMPARE...): định dạng do Phần 2 quyết định,
        # ở đây chỉ kiểm tra region (nếu có) là hợp lệ.
        if clue.region is not None:
            try:
                grid.region_cells(clue.region, size)
            except ValueError as e:
                raise PuzzleError(str(e)) from None


def parse_puzzle(data: dict, default_name: str = "puzzle") -> Puzzle:
    """dict (đã đọc từ JSON) -> Puzzle, có kiểm tra lỗi."""
    if not isinstance(data, dict):
        raise PuzzleError("File puzzle phải là một JSON object {...}")
    for key in ("size", "characters", "initial_revealed"):
        if key not in data:
            raise PuzzleError(f"Thiếu trường bắt buộc '{key}'")

    size = data["size"]
    if not isinstance(size, int) or isinstance(size, bool) or not 1 <= size <= grid.MAX_SIZE:
        raise PuzzleError(f"size phải là số nguyên 1..{grid.MAX_SIZE}, đang là {size!r}")

    raw_chars = data["characters"]
    if not isinstance(raw_chars, list) or len(raw_chars) != size * size:
        n = len(raw_chars) if isinstance(raw_chars, list) else "?"
        raise PuzzleError(f"Lưới {size}x{size} cần đúng {size * size} nhân vật, file có {n}")

    chars: list[Character] = []
    solution: dict[str, Status] = {}
    clues: dict[str, Clue] = {}
    for i, c in enumerate(raw_chars):
        where = f"characters[{i}]"
        if not isinstance(c, dict):
            raise PuzzleError(f"{where} phải là object")
        missing = [k for k in ("cell", "name", "profession", "status", "clue") if k not in c]
        if missing:
            raise PuzzleError(f"{where} thiếu trường {missing}")
        cell = c["cell"]
        where = f"Nhân vật ô {cell!r}"
        if not grid.in_grid(cell, size):
            raise PuzzleError(f"{where}: ô không nằm trong lưới {size}x{size}")
        if cell in solution:
            raise PuzzleError(f"{where}: ô bị trùng (2 nhân vật cùng một ô)")
        try:
            solution[cell] = Status(c["status"])
        except ValueError:
            raise PuzzleError(f"{where}: status phải là CRIMINAL/INNOCENT") from None
        try:
            clue = _clue(f"clue_{cell}", c["clue"])
            _check_clue(clue, size)
        except PuzzleError as e:
            raise PuzzleError(f"{where}: {e}") from None
        clues[cell] = clue
        chars.append(Character(cell, str(c["name"]), str(c["profession"])))

    names = [ch.name for ch in chars]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        raise PuzzleError(f"Tên nhân vật bị trùng: {dup} (đề yêu cầu xếp theo tên nên tên phải khác nhau)")

    init = data["initial_revealed"]
    if not isinstance(init, list) or not init:
        raise PuzzleError("initial_revealed phải là danh sách có ít nhất 1 ô")
    for cell in init:
        if cell not in solution:
            raise PuzzleError(f"initial_revealed có ô không tồn tại: {cell!r}")
    if len(set(init)) != len(init):
        raise PuzzleError(f"initial_revealed có ô bị trùng: {init}")

    chars.sort(key=lambda ch: ch.name)   # đề: nhân vật xếp theo tên (alphabet)
    return Puzzle(str(data.get("name", default_name)), size, chars, solution, clues, list(init))


def load_puzzle(path: str | Path) -> Puzzle:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise PuzzleError(f"File không phải JSON hợp lệ (dòng {e.lineno}, cột {e.colno}): {e.msg}") from None
    return parse_puzzle(data, default_name=path.stem)
