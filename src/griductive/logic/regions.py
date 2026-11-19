"""Phần 2: ROW / COL / NEIGHBORS / CELLS -> danh sách cell id (đã validate)."""
from __future__ import annotations
from ..core.models import Region


def cells_of(region: Region, size: int) -> list[str]:
    """Trả về danh sách cell (không trùng, theo row-major). Raise ValueError nếu sai."""
    raise NotImplementedError


def neighbors(cell: str, size: int) -> list[str]:
    """8 ô kề (ngang/dọc/chéo), bỏ chính nó."""
    raise NotImplementedError
