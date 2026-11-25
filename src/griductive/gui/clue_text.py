"""Clue có cấu trúc -> câu tiếng Việt dễ đọc (Phần 1, chỉ để hiển thị).

Ví dụ: Clue(EXACTLY, k=1, region=ROW "2") -> "Có đúng 1 tội phạm trong hàng 2."
Không có xử lý ngôn ngữ tự nhiên: chỉ là ghép chuỗi theo từng loại clue.
"""
from __future__ import annotations

from typing import Iterable

from ..core.models import Character, Clue, ClueType, Region, RegionKind, Status

STATUS_VI = {Status.CRIMINAL: "TỘI PHẠM", Status.INNOCENT: "VÔ TỘI"}


def _who(cell: str, names: dict[str, str]) -> str:
    """'B1' -> 'Bea (B1)' nếu biết tên, ngược lại chỉ 'B1'."""
    return f"{names[cell]} ({cell})" if cell in names else cell


def region_text(region: Region, names: dict[str, str]) -> str:
    kind = RegionKind(region.kind)
    if kind == RegionKind.ROW:
        return f"hàng {region.ref}"
    if kind == RegionKind.COL:
        return f"cột {region.ref}"
    if kind == RegionKind.NEIGHBORS:
        return f"các ô kề {_who(region.ref, names)}"
    return "các ô " + ", ".join(region.cells)


def _count_sentence(word: str, k: int, where: str) -> str:
    return f"Có {word} {k} tội phạm trong {where}."


def clue_to_text(clue: Clue, characters: Iterable[Character] = ()) -> str:
    names = {c.cell: c.name for c in characters}
    t = ClueType(clue.type)
    tg = clue.targets
    try:
        if t == ClueType.FACT:
            return f"{_who(tg[0], names)} là {STATUS_VI[Status(clue.fact_status)]}."
        if t == ClueType.SAME:
            return (f"{_who(tg[0], names)} và {_who(tg[1], names)} CÙNG trạng thái "
                    "(cùng tội phạm hoặc cùng vô tội).")
        if t == ClueType.DIFFERENT:
            return (f"{_who(tg[0], names)} và {_who(tg[1], names)} KHÁC trạng thái "
                    "(đúng 1 trong 2 người là tội phạm).")
        if t in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
            where = region_text(clue.region, names)
            if t == ClueType.EXACTLY and clue.k == 0:
                return f"Không có tội phạm nào trong {where}."
            word = {ClueType.EXACTLY: "đúng", ClueType.AT_LEAST: "ít nhất",
                    ClueType.AT_MOST: "nhiều nhất"}[t]
            return _count_sentence(word, clue.k, where)
        if t == ClueType.PARITY and clue.region is not None:
            par = str((clue.extra or {}).get("parity", "")).upper()
            kind = {"EVEN": "CHẴN", "ODD": "LẺ"}.get(par, par or "?")
            return f"Số tội phạm trong {region_text(clue.region, names)} là số {kind}."
    except (IndexError, KeyError, TypeError, ValueError):
        pass
    # Clue mở rộng chưa biết định dạng (Phần 2 quyết định) -> hiện dạng thô,
    # không làm sập GUI. Phần 2 có thể bổ sung câu chữ ở đây sau.
    return f"[{t.value}] targets={list(tg)} k={clue.k} extra={clue.extra}"
