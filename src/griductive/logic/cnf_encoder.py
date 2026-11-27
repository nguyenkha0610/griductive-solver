"""CNF Encoder (Phần 2). Hợp đồng với Phần 3 & 4:

    Clause = list[int]              # literal DIMACS, vd [1, -3]
    encode_clue(clue)  -> list[Clause]
    build_kb(state)    -> KnowledgeBase   (CNF(revealed clues) + unit clauses của proved)

KHÔNG hard-code CNF cho từng puzzle. KB không được chứa hidden info.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from ..core.models import Clue, ClueType, PublicState, Region, RegionKind, Status
from .variables import VariableMap
from .regions import cells_of, parse_cell

Clause = list[int]


@dataclass
class KnowledgeBase:
    clauses: list[Clause]
    varmap: VariableMap
    stats: dict = field(default_factory=dict)  # primary_vars, aux_vars, clauses

    @property
    def num_vars(self) -> int:
        return self.varmap.num_primary + self.varmap.num_aux


class CNFEncoder:
    def __init__(self, varmap: VariableMap, size: int):
        self.vm = varmap
        self.size = size

    def validate(self, clue: Clue) -> None:
        """Kiểm tra tham số k (0<=k<=|R|), cell tồn tại, region hợp lệ."""
        if not isinstance(clue, Clue):
            raise TypeError("clue must be a Clue")

        def validate_cell(cell: str) -> None:
            parse_cell(cell, self.size)
            if cell not in self.vm.cell_to_var:
                raise ValueError("clue references unknown cell {!r}".format(cell))

        if clue.type == ClueType.FACT:
            if len(clue.targets) != 1 or clue.fact_status not in (
                Status.CRIMINAL, Status.INNOCENT
            ):
                raise ValueError("FACT requires one target and a valid fact_status")
            for cell in clue.targets:
                validate_cell(cell)
        elif clue.type in (ClueType.SAME, ClueType.DIFFERENT):
            if len(clue.targets) != 2:
                raise ValueError("{} requires exactly two targets".format(clue.type.value))
            for cell in clue.targets:
                validate_cell(cell)
        elif clue.type in (
            ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST, ClueType.PARITY
        ):
            if clue.region is None:
                raise ValueError("{} requires a region".format(clue.type.value))
            region_cells = cells_of(clue.region, self.size)
            for cell in region_cells:
                validate_cell(cell)
            if clue.type == ClueType.PARITY:
                _parity_value(clue)
            else:
                if isinstance(clue.k, bool) or not isinstance(clue.k, int):
                    raise ValueError("{} requires an integer k".format(clue.type.value))
                if clue.k < 0 or clue.k > len(region_cells):
                    raise ValueError("k must be between 0 and the region size")
        elif clue.type == ClueType.COMPARE:
            left = _extra_region(clue.extra, "region_a")
            right = _extra_region(clue.extra, "region_b")
            operator = _compare_operator(clue.extra)
            if operator not in ("=", ">", "<"):
                raise ValueError("COMPARE operator must be '=', '>' or '<'")
            for region in (left, right):
                for cell in cells_of(region, self.size):
                    validate_cell(cell)
        else:
            raise ValueError("unsupported clue type: {!r}".format(clue.type))

    def encode_clue(self, clue: Clue) -> list[Clause]:
        self.validate(clue)
        if clue.type == ClueType.FACT:
            literal = self.vm.var(clue.targets[0])
            return [[literal if clue.fact_status == Status.CRIMINAL else -literal]]
        if clue.type == ClueType.SAME:
            first, second = (self.vm.var(cell) for cell in clue.targets)
            return [[-first, second], [first, -second]]
        if clue.type == ClueType.DIFFERENT:
            first, second = (self.vm.var(cell) for cell in clue.targets)
            return [[first, second], [-first, -second]]
        if clue.type in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
            literals = [self.vm.var(cell) for cell in cells_of(clue.region, self.size)]
            if clue.type == ClueType.EXACTLY:
                return self.encode_exactly(literals, clue.k)
            if clue.type == ClueType.AT_LEAST:
                return self.encode_at_least(literals, clue.k)
            return self.encode_at_most(literals, clue.k)
        if clue.type == ClueType.PARITY:
            literals = [self.vm.var(cell) for cell in cells_of(clue.region, self.size)]
            return self._encode_parity(literals, _parity_value(clue))
        return self._encode_compare(clue)

    def encode_at_least(self, lits: list[int], k: int) -> list[Clause]:
        _validate_cardinality(lits, k)
        return self.encode_at_most([-literal for literal in lits], len(lits) - k)

    def encode_at_most(self, lits: list[int], k: int) -> list[Clause]:
        _validate_cardinality(lits, k)
        if k < 0:
            return [[]]
        if k >= len(lits):
            return []
        if k == 0:
            return [[-literal] for literal in lits]

        # Sequential counter: s[i][j] means the first i+1 inputs contain
        # at least j+1 true literals. It uses O(n*k) auxiliary variables.
        counter = [
            [self.vm.new_aux() for _ in range(k)]
            for _ in range(len(lits) - 1)
        ]
        clauses: list[Clause] = [[-lits[0], counter[0][0]]]
        for index in range(1, len(lits) - 1):
            clauses.extend((
                [-lits[index], counter[index][0]],
                [-counter[index - 1][0], counter[index][0]],
            ))
            for count in range(1, k):
                clauses.extend((
                    [-lits[index], -counter[index - 1][count - 1],
                     counter[index][count]],
                    [-counter[index - 1][count], counter[index][count]],
                ))
        for index in range(1, len(lits)):
            clauses.append([-lits[index], -counter[index - 1][k - 1]])
        return clauses

    def encode_exactly(self, lits: list[int], k: int) -> list[Clause]:
        _validate_cardinality(lits, k)
        return self.encode_at_most(lits, k) + self.encode_at_least(lits, k)

    def _encode_parity(self, lits: list[int], odd: bool) -> list[Clause]:
        if not lits:
            return [[]] if odd else []
        clauses: list[Clause] = []
        previous = lits[0]
        for literal in lits[1:]:
            result = self.vm.new_aux()
            clauses.extend(_xor_equivalence(previous, literal, result))
            previous = result
        clauses.append([previous if odd else -previous])
        return clauses

    def _encode_compare(self, clue: Clue) -> list[Clause]:
        left = [self.vm.var(cell) for cell in cells_of(
            _extra_region(clue.extra, "region_a"), self.size
        )]
        right = [self.vm.var(cell) for cell in cells_of(
            _extra_region(clue.extra, "region_b"), self.size
        )]
        operator = _compare_operator(clue.extra)
        left_selectors, left_constraints = self._count_selectors(left)
        right_selectors, right_constraints = self._count_selectors(right)
        clauses = left_constraints + right_constraints
        clauses.extend(self.encode_exactly(left_selectors, 1))
        clauses.extend(self.encode_exactly(right_selectors, 1))
        for left_count, left_selector in enumerate(left_selectors):
            for right_count, right_selector in enumerate(right_selectors):
                valid = (
                    left_count == right_count if operator == "=" else
                    left_count > right_count if operator == ">" else
                    left_count < right_count
                )
                if not valid:
                    clauses.append([-left_selector, -right_selector])
        return clauses

    def _count_selectors(self, literals: list[int]) -> tuple[list[int], list[Clause]]:
        selectors: list[int] = []
        clauses: list[Clause] = []
        for count in range(len(literals) + 1):
            selector = self.vm.new_aux()
            selectors.append(selector)
            for clause in self.encode_exactly(literals, count):
                clauses.append([-selector] + clause)
        return selectors, clauses


def build_kb(state: PublicState) -> KnowledgeBase:
    """KB_t = CNF(revealed clues) ∧ unit clauses(proved)."""
    varmap = VariableMap(state)
    encoder = CNFEncoder(varmap, state.size)
    clauses: list[Clause] = []
    for clue in state.revealed_clues:
        clauses.extend(encoder.encode_clue(clue))
    for cell, status in state.proved.items():
        if cell not in varmap.cell_to_var:
            raise ValueError("proved status references unknown cell {!r}".format(cell))
        literal = varmap.var(cell)
        clauses.append([literal if status == Status.CRIMINAL else -literal])
    return KnowledgeBase(
        clauses=clauses,
        varmap=varmap,
        stats={
            "primary_vars": varmap.num_primary,
            "aux_vars": varmap.num_aux,
            "clauses": len(clauses),
        },
    )


def _validate_cardinality(lits: list[int], k: int) -> None:
    if isinstance(k, bool) or not isinstance(k, int):
        raise ValueError("k must be an integer")
    if any(isinstance(literal, bool) or not isinstance(literal, int) or literal == 0
           for literal in lits):
        raise ValueError("lits must contain non-zero integer literals")


def _parity_value(clue: Clue) -> bool:
    value = clue.extra.get("parity", clue.extra.get("value"))
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.upper() in ("EVEN", "ODD"):
        return value.upper() == "ODD"
    raise ValueError("PARITY extra.parity must be 'EVEN' or 'ODD'")


def _extra_region(extra: dict, key: str) -> Region:
    value = extra.get(key)
    if isinstance(value, Region):
        return value
    if not isinstance(value, dict) or "kind" not in value:
        raise ValueError("COMPARE requires extra.{}".format(key))
    try:
        kind = RegionKind(value["kind"])
    except ValueError as error:
        raise ValueError("invalid {} region kind".format(key)) from error
    return Region(kind, value.get("ref"), tuple(value.get("cells", ())))


def _compare_operator(extra: dict) -> str:
    operator = extra.get("operator", extra.get("relation"))
    aliases = {"EQ": "=", "EQUAL": "=", "GT": ">", "GREATER": ">",
               "LT": "<", "LESS": "<"}
    if isinstance(operator, str):
        if operator == "==":
            return "="
        return aliases.get(operator.upper(), operator)
    return ""


def _xor_equivalence(first: int, second: int, result: int) -> list[Clause]:
    return [
        [-first, -second, -result],
        [first, second, -result],
        [first, -second, result],
        [-first, second, result],
    ]
