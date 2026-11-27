"""Direct Semantic Evaluator (Phần 2): kiểm tra clue ĐÚNG/SAI với một complete
assignment, KHÔNG gọi CNF encoder. Dùng để test chéo encoder bằng brute force."""
from __future__ import annotations
from ..core.models import Clue, ClueType, Region, RegionKind, Status
from .regions import cells_of


def evaluate_clue(clue: Clue, assignment: dict[str, Status], size: int) -> bool:
    """assignment: cell -> Status (đầy đủ mọi ô)."""
    def criminal(cell: str) -> bool:
        try:
            status = assignment[cell]
        except KeyError as error:
            raise ValueError("assignment is missing cell {!r}".format(cell)) from error
        if not isinstance(status, Status):
            raise ValueError("assignment status for {!r} must be a Status".format(cell))
        return status == Status.CRIMINAL

    if clue.type == ClueType.FACT:
        return criminal(clue.targets[0]) == (clue.fact_status == Status.CRIMINAL)
    if clue.type == ClueType.SAME:
        return criminal(clue.targets[0]) == criminal(clue.targets[1])
    if clue.type == ClueType.DIFFERENT:
        return criminal(clue.targets[0]) != criminal(clue.targets[1])
    if clue.type in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        count = sum(criminal(cell) for cell in cells_of(clue.region, size))
        if clue.type == ClueType.EXACTLY:
            return count == clue.k
        if clue.type == ClueType.AT_LEAST:
            return count >= clue.k
        return count <= clue.k
    if clue.type == ClueType.PARITY:
        count = sum(criminal(cell) for cell in cells_of(clue.region, size))
        parity = clue.extra.get("parity", clue.extra.get("value"))
        odd = parity if isinstance(parity, bool) else (
            parity.upper() == "ODD" if isinstance(parity, str) else None
        )
        if odd is None or (
            isinstance(parity, str) and parity.upper() not in ("EVEN", "ODD")
        ):
            raise ValueError("PARITY extra.parity must be 'EVEN' or 'ODD'")
        return bool(count % 2) == bool(odd)
    if clue.type == ClueType.COMPARE:
        left_region = _region(clue.extra.get("region_a"), "region_a")
        right_region = _region(clue.extra.get("region_b"), "region_b")
        left_count = sum(criminal(cell) for cell in cells_of(left_region, size))
        right_count = sum(criminal(cell) for cell in cells_of(right_region, size))
        operator = clue.extra.get("operator", clue.extra.get("relation"))
        operator = operator.upper() if isinstance(operator, str) else operator
        if operator in ("=", "EQ", "EQUAL", "=="):
            return left_count == right_count
        if operator in (">", "GT", "GREATER"):
            return left_count > right_count
        if operator in ("<", "LT", "LESS"):
            return left_count < right_count
        raise ValueError("COMPARE operator must be '=', '>' or '<'")
    raise ValueError("unsupported clue type: {!r}".format(clue.type))


def _region(value: Region | dict, key: str) -> Region:
    if isinstance(value, Region):
        return value
    if not isinstance(value, dict) or "kind" not in value:
        raise ValueError("COMPARE requires extra.{}".format(key))
    try:
        return Region(
            RegionKind(value["kind"]),
            value.get("ref"),
            tuple(value.get("cells", ())),
        )
    except ValueError as error:
        raise ValueError("invalid {} region".format(key)) from error
