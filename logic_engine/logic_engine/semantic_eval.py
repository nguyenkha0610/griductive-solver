"""Đánh giá ngữ nghĩa trực tiếp, độc lập với CNF."""
from clues import ClueType, validate


def evaluate(clue, assignment, n):
    """assignment: dict {(r, c): bool} cho toàn bộ lưới."""
    cells = validate(clue, n)
    vals = [bool(assignment[c]) for c in cells]
    cnt, t, v = sum(vals), clue.type, clue.value
    if t == ClueType.FACT:
        return vals[0] == v
    if t == ClueType.SAME:
        return len(set(vals)) == 1
    if t == ClueType.DIFFERENT:
        return len(set(vals)) == 2
    if t == ClueType.EXACTLY:
        return cnt == v
    if t == ClueType.AT_LEAST:
        return cnt >= v
    if t == ClueType.AT_MOST:
        return cnt <= v
    if t == ClueType.BETWEEN:
        return v[0] <= cnt <= v[1]
    if t == ClueType.PARITY:
        return cnt % 2 == v
    raise ValueError(t)
