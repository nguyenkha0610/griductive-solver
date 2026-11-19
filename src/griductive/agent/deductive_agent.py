"""Deductive Logic Agent (Phần 4). Chỉ nhận PublicState, KHÔNG biết hidden solution.

    classify(state, cell) -> Verdict
        UNSAT(KB ∧ ¬C_i) -> CRIMINAL ; UNSAT(KB ∧ C_i) -> INNOCENT ;
        cả hai SAT -> UNKNOWN ; KB UNSAT -> INCONSISTENT
    hint(state) -> (cell, Verdict) | None
    auto_solve(engine) -> DeductionTrace      (row-major khi nhiều ô cùng forced)
"""
from __future__ import annotations
from ..core.models import PublicState, Verdict
from .trace import DeductionTrace


class DeductiveAgent:
    def classify(self, state: PublicState, cell: str) -> Verdict:
        raise NotImplementedError

    def classify_all(self, state: PublicState) -> dict[str, Verdict]:
        raise NotImplementedError

    def hint(self, state: PublicState):
        raise NotImplementedError

    def auto_solve(self, engine) -> DeductionTrace:
        raise NotImplementedError
