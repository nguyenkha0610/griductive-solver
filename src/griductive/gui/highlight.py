"""Tìm các ô mà một clue nhắc tới / đếm, để GUI tô sáng (Phần 1).

Ưu tiên dùng `logic.regions.cells_of` (Phần 2). Nếu Phần 2 chưa cài
(NotImplementedError) thì dùng hàm phụ `core.grid.region_cells`.
=> Khi Phần 2 xong, GUI tự dùng hàm của Phần 2, không phải sửa gì ở đây.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core import grid
from ..core.models import Clue, Region, RegionKind


def region_cells(region: Region, size: int) -> list[str]:
    try:
        from ..logic.regions import cells_of
        return list(cells_of(region, size))
    except NotImplementedError:
        return grid.region_cells(region, size)


def clue_owner(clue: Clue) -> str:
    """Clue id 'clue_B2' -> ô 'B2' (ô của người giữ thẻ này)."""
    return clue.id[len("clue_"):] if clue.id.startswith("clue_") else clue.id


@dataclass(frozen=True)
class Highlight:
    counted: frozenset[str]     # các ô được ĐẾM / nhắc tới (tô đậm)
    anchors: frozenset[str]     # ô "mốc", vd ô tâm của NEIGHBORS (tô nhạt)

    @property
    def all(self) -> frozenset[str]:
        return self.counted | self.anchors


def _regions_in(clue: Clue) -> list[Region]:
    """Mọi vùng trong clue: clue.region + vùng nằm trong `extra` (clue mở rộng,
    vd COMPARE có 2 vùng). Vùng trong extra là dict {"kind":..., "ref"/"cells":...}."""
    out = [clue.region] if clue.region is not None else []
    for v in (clue.extra or {}).values():
        if isinstance(v, Region):
            out.append(v)
        elif isinstance(v, dict) and "kind" in v:
            try:
                out.append(Region(RegionKind(v["kind"]), v.get("ref"), tuple(v.get("cells", []))))
            except ValueError:
                pass
    return out


def clue_highlight(clue: Clue, size: int) -> Highlight:
    counted: set[str] = set(clue.targets)
    anchors: set[str] = set()
    for reg in _regions_in(clue):
        try:
            counted.update(region_cells(reg, size))
        except ValueError:
            continue          # vùng lỗi: bỏ qua, không làm sập GUI
        if reg.kind == RegionKind.NEIGHBORS and reg.ref:
            anchors.add(reg.ref)
    return Highlight(frozenset(counted), frozenset(anchors - counted))
