"""CNF Encoder (Phần 2). Hợp đồng với Phần 3 & 4:

    Clause = list[int]              # literal DIMACS, vd [1, -3]
    encode_clue(clue)  -> list[Clause]
    build_kb(state)    -> KnowledgeBase   (CNF(revealed clues) + unit clauses của proved)

KHÔNG hard-code CNF cho từng puzzle. KB không được chứa hidden info.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from ..core.models import Clue, PublicState
from .variables import VariableMap

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
        raise NotImplementedError

    def encode_clue(self, clue: Clue) -> list[Clause]:
        raise NotImplementedError

    def encode_at_least(self, lits: list[int], k: int) -> list[Clause]: raise NotImplementedError
    def encode_at_most(self, lits: list[int], k: int) -> list[Clause]: raise NotImplementedError
    def encode_exactly(self, lits: list[int], k: int) -> list[Clause]: raise NotImplementedError


def build_kb(state: PublicState) -> KnowledgeBase:
    """KB_t = CNF(revealed clues) ∧ unit clauses(proved)."""
    raise NotImplementedError
