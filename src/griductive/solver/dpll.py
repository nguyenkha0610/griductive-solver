"""A small, deterministic DPLL solver for DIMACS-style integer CNF."""
from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Optional, Sequence


@dataclass
class SolverStats:
    """Counters collected during one solve call."""

    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0
    runtime: float = 0.0


@dataclass
class SolveResult:
    """Result for a solve call; a model is present only when the formula is SAT."""

    sat: bool
    model: Optional[dict[int, bool]] = None
    stats: SolverStats = field(default_factory=SolverStats)
    trace: tuple[str, ...] = ()

    @property
    def status(self) -> str:
        """Return the conventional SAT/UNSAT status string."""
        return "SAT" if self.sat else "UNSAT"

    @property
    def assignment(self) -> Optional[dict[int, bool]]:
        """Alias for ``model`` for callers that prefer assignment terminology."""
        return self.model

    @property
    def decisions(self) -> int:
        return self.stats.decisions

    @property
    def propagations(self) -> int:
        return self.stats.propagations

    @property
    def backtracks(self) -> int:
        return self.stats.backtracks

    @property
    def runtime(self) -> float:
        return self.stats.runtime


class DPLLSolver:
    """Solve CNF formulas using unit propagation and recursive DPLL search.

    Variables are positive integers, literals are signed integers, clauses are
    sequences of literals, and a CNF formula is a sequence of clauses.
    """

    def __init__(self, num_vars: Optional[int] = None, trace: bool = False):
        if num_vars is not None:
            self._validate_num_vars(num_vars)
        self.num_vars = num_vars
        self.trace_enabled = trace

    def solve(
        self,
        clauses: Sequence[Sequence[int]],
        num_vars: Optional[int] = None,
        assumptions: Sequence[int] = (),
    ) -> SolveResult:
        """Return a SAT model or UNSAT, optionally under temporary assumptions.

        ``num_vars`` can retain declared-but-unused variables in a complete
        model. If omitted, the variable count is inferred from the formula and
        assumptions. Neither the caller's clauses nor assumptions are mutated.
        """
        started = perf_counter()
        stats = SolverStats()
        events: list[str] = []

        def record(message: str) -> None:
            if self.trace_enabled:
                events.append(message)

        requested_vars = num_vars if num_vars is not None else self.num_vars
        if requested_vars is not None:
            self._validate_num_vars(requested_vars)
        validated_clauses = self._validate_clauses(clauses)
        validated_assumptions = self._validate_assumptions(assumptions)
        max_literal_var = max(
            [abs(literal) for clause in validated_clauses for literal in clause]
            + [abs(literal) for literal in validated_assumptions]
            + [0]
        )
        variable_count = max_literal_var if requested_vars is None else requested_vars
        if variable_count < max_literal_var:
            raise ValueError("num_vars is smaller than a variable used by CNF or assumptions")

        formula = self._normalize(validated_clauses)
        assignment: dict[int, bool] = {}
        for literal in validated_assumptions:
            variable, value = abs(literal), literal > 0
            previous = assignment.get(variable)
            if previous is not None and previous != value:
                record("CONFLICT: contradictory assumptions")
                stats.runtime = perf_counter() - started
                return SolveResult(False, None, stats, tuple(events))
            assignment[variable] = value
            record("ASSUMPTION: variable {} = {}".format(
                variable, str(value).lower()
            ))

        def propagate(current: dict[int, bool]) -> bool:
            """Apply unit assignments until stable; return False on conflict."""
            while True:
                unit_literal: Optional[int] = None
                for clause in formula:
                    unresolved: list[int] = []
                    satisfied = False
                    for literal in clause:
                        value = current.get(abs(literal))
                        if value is None:
                            unresolved.append(literal)
                        elif value == (literal > 0):
                            satisfied = True
                            break
                    if satisfied:
                        continue
                    if not unresolved:
                        record("CONFLICT: clause {} is false".format(list(clause)))
                        return False
                    if len(unresolved) == 1:
                        unit_literal = unresolved[0]
                        break

                if unit_literal is None:
                    return True

                variable, value = abs(unit_literal), unit_literal > 0
                previous = current.get(variable)
                if previous is not None:
                    if previous != value:
                        record("CONFLICT: variable {} required both values".format(
                            variable
                        ))
                        return False
                    continue
                current[variable] = value
                stats.propagations += 1
                record("PROPAGATE: variable {} = {}".format(
                    variable, str(value).lower()
                ))

        def search(current: dict[int, bool]) -> Optional[dict[int, bool]]:
            if not propagate(current):
                return None

            unresolved_variables: set[int] = set()
            for clause in formula:
                clause_satisfied = False
                for literal in clause:
                    value = current.get(abs(literal))
                    if value is not None and value == (literal > 0):
                        clause_satisfied = True
                        break
                if not clause_satisfied:
                    unresolved_variables.update(
                        abs(literal) for literal in clause
                        if abs(literal) not in current
                    )

            if not unresolved_variables:
                completed = dict(current)
                for variable in range(1, variable_count + 1):
                    completed.setdefault(variable, False)
                return completed

            variable = min(unresolved_variables)
            for value in (True, False):
                stats.decisions += 1
                record("DECIDE: variable {} = {}".format(
                    variable, str(value).lower()
                ))
                branch = dict(current)
                branch[variable] = value
                result = search(branch)
                if result is not None:
                    return result
                stats.backtracks += 1
                record("BACKTRACK: variable {} = {} failed".format(
                    variable, str(value).lower()
                ))
            return None

        model = search(assignment)
        stats.runtime = perf_counter() - started
        return SolveResult(model is not None, model, stats, tuple(events))

    @staticmethod
    def _validate_num_vars(num_vars: int) -> None:
        if isinstance(num_vars, bool) or not isinstance(num_vars, int) or num_vars < 0:
            raise ValueError("num_vars must be a non-negative integer")

    @classmethod
    def _validate_clauses(
        cls, clauses: Sequence[Sequence[int]]
    ) -> tuple[tuple[int, ...], ...]:
        try:
            result = tuple(tuple(clause) for clause in clauses)
        except TypeError as error:
            raise ValueError("CNF must be a sequence of clauses") from error
        for clause in result:
            for literal in clause:
                if isinstance(literal, bool) or not isinstance(literal, int) or literal == 0:
                    raise ValueError("literals must be non-zero integers")
        return result

    @staticmethod
    def _validate_assumptions(assumptions: Sequence[int]) -> tuple[int, ...]:
        try:
            result = tuple(assumptions)
        except TypeError as error:
            raise ValueError("assumptions must be a sequence of literals") from error
        for literal in result:
            if isinstance(literal, bool) or not isinstance(literal, int) or literal == 0:
                raise ValueError("assumptions must be non-zero integer literals")
        return result

    @staticmethod
    def _normalize(
        clauses: tuple[tuple[int, ...], ...]
    ) -> tuple[tuple[int, ...], ...]:
        """Remove duplicate literals and tautological clauses without mutation."""
        normalized: list[tuple[int, ...]] = []
        for clause in clauses:
            unique = tuple(dict.fromkeys(clause))
            if any(-literal in unique for literal in unique):
                continue
            normalized.append(unique)
        return tuple(normalized)


def solve(
    clauses: Sequence[Sequence[int]],
    num_vars: int,
    assumptions: Sequence[int] = (),
) -> SolveResult:
    """Backward-compatible function API used by the Part 4 contract."""
    return DPLLSolver(num_vars=num_vars).solve(clauses, assumptions=assumptions)
