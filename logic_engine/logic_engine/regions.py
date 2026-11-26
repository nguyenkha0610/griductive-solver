"""Xác định vùng: hàng, cột, ô lân cận, danh sách tùy chỉnh."""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Region:
    kind: str                 # "row" | "col" | "neighbors" | "custom"
    params: Tuple = ()


def row(r):
    return Region("row", (r,))


def col(c):
    return Region("col", (c,))


def neighbors(r, c, diagonal=True):
    return Region("neighbors", (r, c, diagonal))


def custom(cells):
    return Region("custom", tuple(tuple(x) for x in cells))


def get_cells(region, n):
    """Trả về danh sách ô (r, c) thuộc vùng, trong lưới n x n."""
    k, p = region.kind, region.params
    if k == "row":
        cells = [(p[0], c) for c in range(n)]
    elif k == "col":
        cells = [(r, p[0]) for r in range(n)]
    elif k == "neighbors":
        r0, c0, diag = p
        cells = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dr, dc) == (0, 0) or (not diag and dr != 0 and dc != 0):
                    continue
                r, c = r0 + dr, c0 + dc
                if 0 <= r < n and 0 <= c < n:
                    cells.append((r, c))
    elif k == "custom":
        cells = list(p)
    else:
        raise ValueError(f"Loại vùng không hợp lệ: {k}")
    return cells
