"""Direct Semantic Evaluator (Phần 2): kiểm tra clue ĐÚNG/SAI với một complete
assignment, KHÔNG gọi CNF encoder. Dùng để test chéo encoder bằng brute force."""
from __future__ import annotations
from ..core.models import Clue, Status


def evaluate_clue(clue: Clue, assignment: dict[str, Status], size: int) -> bool:
    """assignment: cell -> Status (đầy đủ mọi ô)."""
    raise NotImplementedError
