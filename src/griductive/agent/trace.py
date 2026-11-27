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
    runtime: float = 0.0


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

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation of the deduction trace."""
        return {
            "terminal": self.terminal,
            "steps": [
                {
                    "step": step.step,
                    "active_clue_ids": list(step.active_clue_ids),
                    "queries": [
                        {
                            "cell": query.cell,
                            "assumption": query.assumption,
                            "result": query.result,
                            "decisions": query.decisions,
                            "propagations": query.propagations,
                            "backtracks": query.backtracks,
                            "runtime": query.runtime,
                        }
                        for query in step.queries
                    ],
                    "cell": step.cell,
                    "verdict": step.verdict.value if step.verdict else None,
                    "revealed_clue_id": step.revealed_clue_id,
                }
                for step in self.steps
            ],
        }
