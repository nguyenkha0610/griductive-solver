"""Tiện ích tọa độ lưới (Phần 1).

Cell id dạng "B3": chữ cái = CỘT (A, B, C... từ trái sang),
                   số      = HÀNG (1, 2, 3... từ trên xuống).

File này dùng cho: kiểm tra file puzzle (puzzle_io) và GUI (vẽ lưới, tô sáng).
Hàm "chính thức" để tính vùng cho Encoder là `logic/regions.cells_of` (Phần 2).
GUI ưu tiên gọi hàm của Phần 2; chỉ khi Phần 2 chưa xong mới dùng `region_cells`
ở đây (xem gui/highlight.py).
"""
from __future__ import annotations

import re

from .models import Region, RegionKind

MAX_SIZE = 9   # hàng chỉ có 1 chữ số -> lưới tối đa 9x9 (đề chỉ cần 3..5)
_CELL_RE = re.compile(r"^([A-Z])([1-9])$")


def col_letters(size: int) -> list[str]:
    """size=3 -> ['A', 'B', 'C']"""
    return [chr(ord("A") + i) for i in range(size)]


def parse_cell(cell: str) -> tuple[int, int]:
    """'B3' -> (row=3, col=2)  (đánh số từ 1). Sai định dạng -> ValueError."""
    m = _CELL_RE.match(cell) if isinstance(cell, str) else None
    if not m:
        raise ValueError(f"Tên ô không hợp lệ: {cell!r} (đúng dạng là 'A1', 'C3'...)")
    return int(m.group(2)), ord(m.group(1)) - ord("A") + 1


def make_cell(row: int, col: int) -> str:
    """(row=3, col=2) -> 'B3'"""
    return f"{chr(ord('A') + col - 1)}{row}"


def in_grid(cell: str, size: int) -> bool:
    try:
        r, c = parse_cell(cell)
    except ValueError:
        return False
    return 1 <= r <= size and 1 <= c <= size


def all_cells(size: int) -> list[str]:
    """Mọi ô theo thứ tự row-major (đọc như đọc sách: hết hàng 1 rồi tới hàng 2)."""
    return [make_cell(r, c) for r in range(1, size + 1) for c in range(1, size + 1)]


def neighbors(cell: str, size: int) -> list[str]:
    """8 ô xung quanh (ngang, dọc, chéo), bỏ chính nó, theo row-major."""
    r0, c0 = parse_cell(cell)
    out = []
    for r in range(r0 - 1, r0 + 2):
        for c in range(c0 - 1, c0 + 2):
            if (r, c) != (r0, c0) and 1 <= r <= size and 1 <= c <= size:
                out.append(make_cell(r, c))
    return out


def region_cells(region: Region, size: int) -> list[str]:
    """Danh sách ô của một vùng (ROW / COL / NEIGHBORS / CELLS), row-major.
    Vùng sai (hàng/cột/ô không tồn tại, CELLS trùng hoặc rỗng) -> ValueError."""
    kind = RegionKind(region.kind)
    if kind == RegionKind.ROW:
        if region.ref not in [str(i) for i in range(1, size + 1)]:
            raise ValueError(f"Hàng không tồn tại: {region.ref!r}")
        return [c for c in all_cells(size) if c[1:] == region.ref]
    if kind == RegionKind.COL:
        if region.ref not in col_letters(size):
            raise ValueError(f"Cột không tồn tại: {region.ref!r}")
        return [c for c in all_cells(size) if c[0] == region.ref]
    if kind == RegionKind.NEIGHBORS:
        if not in_grid(region.ref, size):
            raise ValueError(f"Ô tâm của NEIGHBORS không tồn tại: {region.ref!r}")
        return neighbors(region.ref, size)
    # CELLS
    cells = list(region.cells)
    if not cells:
        raise ValueError("Vùng CELLS rỗng")
    bad = [c for c in cells if not in_grid(c, size)]
    if bad:
        raise ValueError(f"Vùng CELLS có ô không tồn tại: {bad}")
    if len(set(cells)) != len(cells):
        raise ValueError(f"Vùng CELLS có ô bị trùng: {cells}")
    order = {c: i for i, c in enumerate(all_cells(size))}
    return sorted(cells, key=order.__getitem__)
