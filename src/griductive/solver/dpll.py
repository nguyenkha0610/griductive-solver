"""DPLL tự cài đặt (Phần 3). Hợp đồng với Phần 4:

    solve(clauses, num_vars, assumptions=()) -> SolveResult

Bắt buộc: unit propagation, conflict detection, chọn biến deterministic,
đệ quy + backtrack, trả complete assignment (mọi biến 1..num_vars), ghi stats.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Sequence


@dataclass
class SolverStats:
    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0
    runtime: float = 0.0


@dataclass
class SolveResult:
    sat: bool
    model: Optional[dict[int, bool]] = None   # var -> bool (complete) nếu SAT
    stats: SolverStats = field(default_factory=SolverStats)


def solve(clauses: Sequence[Sequence[int]], num_vars: int,
          assumptions: Sequence[int] = ()) -> SolveResult:
    raise NotImplementedError
