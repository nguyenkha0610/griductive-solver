"""Cấu trúc dữ liệu dùng chung cho TOÀN BỘ nhóm. Sửa file này phải báo cả nhóm.

Cell id: chuỗi "A1".."E5" (cột = chữ cái, hàng = số, hàng đánh số từ trên xuống).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Status(str, Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"


class Verdict(str, Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"
    INCONSISTENT = "INCONSISTENT"


class SubmitResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    NOT_PROVABLE = "NOT_PROVABLE"
    CONTRADICTED = "CONTRADICTED"
    ALREADY_REVEALED = "ALREADY_REVEALED"
    INCONSISTENT = "INCONSISTENT"


class ClueType(str, Enum):
    # 6 loại bắt buộc
    FACT = "FACT"
    SAME = "SAME"
    DIFFERENT = "DIFFERENT"
    EXACTLY = "EXACTLY"
    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"
    # >= 2 loại mở rộng (Phần 2 chọn/đổi tên): gợi ý parity + so sánh số lượng
    PARITY = "PARITY"        # số Criminal trong vùng là chẵn/lẻ
    COMPARE = "COMPARE"      # count(region_a) > / = / < count(region_b)


class RegionKind(str, Enum):
    ROW = "ROW"              # ref = "3"
    COL = "COL"              # ref = "B"
    NEIGHBORS = "NEIGHBORS"  # ref = "B2" (8 hướng, bỏ chính nó)
    CELLS = "CELLS"          # cells = ["A1","C3",...]


@dataclass(frozen=True)
class Region:
    kind: RegionKind
    ref: Optional[str] = None
    cells: tuple[str, ...] = ()


@dataclass(frozen=True)
class Clue:
    """Clue có cấu trúc. Dùng cho JSON -> Clue -> Encoder/Evaluator."""
    id: str                          # ví dụ "clue_C1" (= clue của ô C1)
    type: ClueType
    targets: tuple[str, ...] = ()    # FACT: (cell,) | SAME/DIFFERENT: (cell_i, cell_j)
    fact_status: Optional[Status] = None   # chỉ dùng cho FACT
    region: Optional[Region] = None  # EXACTLY / AT_LEAST / AT_MOST / PARITY
    k: Optional[int] = None
    extra: dict = field(default_factory=dict)  # tham số cho clue mở rộng


@dataclass(frozen=True)
class Character:
    cell: str
    name: str
    profession: str


@dataclass(frozen=True)
class PublicState:
    """Thứ DUY NHẤT Logic Agent được nhìn thấy. Không chứa hidden solution
    hay clue của thẻ chưa lật."""
    size: int
    characters: tuple[Character, ...]            # sắp xếp theo tên (alphabet)
    revealed_clues: tuple[Clue, ...]
    proved: dict[str, Status] = field(default_factory=dict)  # cell -> status
