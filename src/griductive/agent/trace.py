from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..core.models import Verdict


@dataclass
class SatQuery:
    cell: str
    assumption: str          # "KB ∧ ¬C_i" hoặc "KB ∧ C_i"
    result: str              # "SAT" / "UNSAT"
    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0


@dataclass
class TraceStep:
    step: int
    active_clue_ids: list[str]
    queries: list[SatQuery] = field(default_factory=list)
    cell: Optional[str] = None
    verdict: Optional[Verdict] = None
    revealed_clue_id: Optional[str] = None


@dataclass
class DeductionTrace:
    steps: list[TraceStep] = field(default_factory=list)
    terminal: str = ""       # SOLVED | STUCK | INCONSISTENT
