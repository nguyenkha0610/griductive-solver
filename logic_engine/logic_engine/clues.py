"""Định nghĩa Clue và kiểm tra tham số."""
from dataclasses import dataclass
from enum import Enum
from typing import Any
from regions import Region, get_cells


class ClueType(Enum):
    # Bắt buộc
    FACT = "FACT"            # ô duy nhất có giá trị value (bool)
    SAME = "SAME"            # mọi ô trong vùng cùng giá trị
    DIFFERENT = "DIFFERENT"  # vùng có cả ô True lẫn ô False
    EXACTLY = "EXACTLY"      # số ô True == value
    AT_LEAST = "AT_LEAST"    # số ô True >= value
    AT_MOST = "AT_MOST"      # số ô True <= value
    # Mở rộng
    BETWEEN = "BETWEEN"      # lo <= số ô True <= hi, value = (lo, hi)
    PARITY = "PARITY"        # số ô True chẵn (0) hoặc lẻ (1), value = 0/1


@dataclass(frozen=True)
class Clue:
    type: ClueType
    region: Region
    value: Any = None


def validate(clue, n):
    """Ném ValueError nếu tham số hoặc vùng không hợp lệ."""
    if not isinstance(clue.type, ClueType):
        raise ValueError("Loại clue không hợp lệ")
    cells = get_cells(clue.region, n)
    if not cells:
        raise ValueError("Vùng rỗng")
    if len(set(cells)) != len(cells):
        raise ValueError("Vùng chứa ô trùng lặp")
    for r, c in cells:
        if not (0 <= r < n and 0 <= c < n):
            raise ValueError(f"Ô {(r, c)} nằm ngoài lưới {n}x{n}")
    t, v, m = clue.type, clue.value, len(cells)
    if t == ClueType.FACT:
        if m != 1 or not isinstance(v, bool):
            raise ValueError("FACT cần đúng 1 ô và value kiểu bool")
    elif t in (ClueType.SAME, ClueType.DIFFERENT):
        if m < 2:
            raise ValueError(f"{t.value} cần vùng có >= 2 ô")
    elif t in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        if not isinstance(v, int) or isinstance(v, bool) or not (0 <= v <= m):
            raise ValueError(f"{t.value}: value phải là số nguyên trong [0, {m}]")
    elif t == ClueType.BETWEEN:
        if not (isinstance(v, tuple) and len(v) == 2 and 0 <= v[0] <= v[1] <= m):
            raise ValueError(f"BETWEEN: value phải là (lo, hi) với 0 <= lo <= hi <= {m}")
    elif t == ClueType.PARITY:
        if v not in (0, 1):
            raise ValueError("PARITY: value phải là 0 (chẵn) hoặc 1 (lẻ)")
    return cells
