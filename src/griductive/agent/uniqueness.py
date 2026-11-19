"""Uniqueness Check (Phần 4): với TOÀN BỘ clue set của puzzle (dùng để validate
puzzle, tách khỏi game). Trả: 0 / 1 / >=2 nghiệm.
Gợi ý: tìm 1 model, thêm blocking clause trên primary vars, giải lại."""
from __future__ import annotations
from ..core.models import Clue


def count_solutions(all_clues: list[Clue], characters_state, limit: int = 2) -> int:
    raise NotImplementedError
