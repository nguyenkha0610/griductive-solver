"""!!! CHỈ DÙNG ĐỂ DEV — SẼ THAY BẰNG DeductiveAgent.classify (Phần 4) !!!

Classifier tạm để test GUI trong lúc Phần 2/4 chưa xong. GUI chỉ gọi file này khi
DeductiveAgent.classify còn raise NotImplementedError.

Cách làm: "thử hết mọi khả năng" (brute force).
  - Đầu vào DUY NHẤT là PublicState (clue đã lật + verdict đã chứng minh).
    KHÔNG đọc đáp án ẩn, KHÔNG đọc clue chưa lật.
  - Chỉ thử các ô chưa biết mà clue đã lật có nhắc tới (ô không được nhắc tới
    thì chắc chắn là UNKNOWN).
  - Giữ lại các cách gán thỏa MỌI clue đã lật. Nếu ô X có cùng giá trị trong mọi
    cách gán còn lại -> X bị ép buộc (CRIMINAL/INNOCENT); không thì UNKNOWN.
  - Không còn cách gán nào -> INCONSISTENT.
Đây KHÔNG phải CNF/DPLL như đề yêu cầu; bản nộp phải dùng agent của Phần 4.
"""
from __future__ import annotations

from itertools import product

from ..core.models import Clue, ClueType, PublicState, Status, Verdict
from .highlight import clue_highlight, region_cells

MAX_FREE_CELLS = 20      # 2^20 ≈ 1 triệu cách gán: lớn hơn thì từ chối


def _holds(clue: Clue, crim: dict[str, bool], size: int) -> bool:
    """Clue có đúng với cách gán `crim` (cell -> True nếu tội phạm) không."""
    t = ClueType(clue.type)
    if t == ClueType.FACT:
        return crim[clue.targets[0]] == (Status(clue.fact_status) == Status.CRIMINAL)
    if t == ClueType.SAME:
        return crim[clue.targets[0]] == crim[clue.targets[1]]
    if t == ClueType.DIFFERENT:
        return crim[clue.targets[0]] != crim[clue.targets[1]]
    if t in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        n = sum(crim[c] for c in region_cells(clue.region, size))
        return {ClueType.EXACTLY: n == clue.k, ClueType.AT_LEAST: n >= clue.k,
                ClueType.AT_MOST: n <= clue.k}[t]
    raise NotImplementedError(f"dev_classifier chưa hỗ trợ clue {t.value}")


def _models(state: PublicState):
    """Sinh từng cách gán (chỉ trên các ô liên quan) thỏa mọi clue đã lật."""
    known = {c: s == Status.CRIMINAL for c, s in state.proved.items()}
    mentioned: set[str] = set()
    for clue in state.revealed_clues:
        mentioned |= clue_highlight(clue, state.size).counted
    free = sorted(mentioned - set(known))
    if len(free) > MAX_FREE_CELLS:
        raise RuntimeError(f"dev_classifier: quá nhiều ô chưa biết ({len(free)})")
    for values in product((False, True), repeat=len(free)):
        crim = dict(known)
        crim.update(zip(free, values))
        if all(_holds(cl, crim, state.size) for cl in state.revealed_clues):
            yield crim, free


def dev_classify(state: PublicState, cell: str) -> Verdict:
    seen: set[bool] = set()
    any_model = False
    for crim, free in _models(state):
        any_model = True
        if cell not in free and cell not in crim:
            return Verdict.UNKNOWN       # không clue nào nhắc tới ô này
        seen.add(crim[cell])
        if len(seen) == 2:
            return Verdict.UNKNOWN
    if not any_model:
        return Verdict.INCONSISTENT
    return Verdict.CRIMINAL if seen == {True} else Verdict.INNOCENT
