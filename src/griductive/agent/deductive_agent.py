"""SAT-based deductive agent; it only consumes the engine's public state."""
from __future__ import annotations

from collections.abc import Sequence

from ..core.engine import GameEngine
from ..core.models import Character, Clue, PublicState, Status, SubmitResult, Verdict
from ..logic.cnf_encoder import KnowledgeBase, build_kb
from ..logic.regions import parse_cell
from ..solver.dpll import DPLLSolver, SolveResult
from .trace import DeductionTrace, SatQuery, TraceStep
from .uniqueness import check_uniqueness as _check_uniqueness


class DeductiveAgent:
    def __init__(self) -> None:
        self._solver = DPLLSolver()

    def classify(self, state: PublicState, cell: str) -> Verdict:
        """Return a verdict only when it is entailed by the public knowledge base."""
        self._validate_cell(state, cell)
        knowledge = build_kb(state)
        if not self._solver.solve(
            knowledge.clauses, num_vars=knowledge.num_vars
        ).sat:
            return Verdict.INCONSISTENT
        return self._classify_consistent(knowledge, cell)

    def classify_all(self, state: PublicState) -> dict[str, Verdict]:
        """Classify every character in stable row-major order."""
        cells = self._ordered_cells(state)
        knowledge = build_kb(state)
        if not self._solver.solve(
            knowledge.clauses, num_vars=knowledge.num_vars
        ).sat:
            return {cell: Verdict.INCONSISTENT for cell in cells}
        return {
            cell: self._classify_consistent(knowledge, cell)
            for cell in cells
        }

    def hint(self, state: PublicState) -> tuple[str, Verdict] | None:
        """Return the first forced, unrevealed cell without reading hidden data."""
        classifications = self.classify_all(state)
        for cell in self._ordered_cells(state):
            verdict = classifications[cell]
            if cell not in state.proved and verdict in (
                Verdict.CRIMINAL, Verdict.INNOCENT
            ):
                return cell, verdict
        return None

    @staticmethod
    def check_uniqueness(
        all_clues: list[Clue],
        characters_state: PublicState | Sequence[Character],
    ) -> bool:
        """Check that the complete clue set has exactly one primary solution."""
        return _check_uniqueness(all_clues, characters_state)

    def auto_solve(self, engine: GameEngine) -> DeductionTrace:
        """Submit one forced verdict per round, revealing a new clue each time."""
        trace = DeductionTrace()
        while True:
            state = engine.public_state()
            knowledge = build_kb(state)
            step = TraceStep(
                step=len(trace.steps) + 1,
                active_clue_ids=[clue.id for clue in state.revealed_clues],
            )
            consistency = self._solve(knowledge, ())
            step.queries.append(self._query("", "KB", consistency))
            if not consistency.sat:
                trace.steps.append(step)
                trace.terminal = "INCONSISTENT"
                return trace
            if engine.is_solved():
                trace.steps.append(step)
                trace.terminal = "SOLVED"
                return trace

            classifications: dict[str, Verdict] = {}
            for cell in self._ordered_cells(state):
                if cell in state.proved:
                    continue
                variable = knowledge.varmap.var(cell)
                criminal_query = self._solve(knowledge, (-variable,))
                step.queries.append(self._query(
                    cell, "KB AND NOT C_i", criminal_query
                ))
                innocent_query = self._solve(knowledge, (variable,))
                step.queries.append(self._query(
                    cell, "KB AND C_i", innocent_query
                ))
                if not criminal_query.sat:
                    classifications[cell] = Verdict.CRIMINAL
                elif not innocent_query.sat:
                    classifications[cell] = Verdict.INNOCENT
                else:
                    classifications[cell] = Verdict.UNKNOWN

            forced = next(
                (
                    (cell, classifications[cell])
                    for cell in self._ordered_cells(state)
                    if cell in classifications
                    and classifications[cell] in (
                        Verdict.CRIMINAL, Verdict.INNOCENT
                    )
                ),
                None,
            )
            if forced is None:
                trace.steps.append(step)
                trace.terminal = "STUCK"
                return trace

            cell, verdict = forced
            step.cell = cell
            step.verdict = verdict
            claimed = (
                Status.CRIMINAL if verdict == Verdict.CRIMINAL else Status.INNOCENT
            )
            result = engine.submit_verdict(
                cell,
                claimed,
                lambda _state, target: classifications[target],
            )
            if result == SubmitResult.INCONSISTENT:
                trace.steps.append(step)
                trace.terminal = "INCONSISTENT"
                return trace
            if result != SubmitResult.ACCEPTED:
                raise RuntimeError(
                    "forced verdict for {} was rejected by the game engine: {}".format(
                        cell, result.value
                    )
                )
            step.revealed_clue_id = engine.get_clue(cell).id
            trace.steps.append(step)
            if engine.is_solved():
                final_knowledge = build_kb(engine.public_state())
                final_result = self._solve(final_knowledge, ())
                step.queries.append(self._query(
                    "", "KB after final reveal", final_result
                ))
                trace.terminal = (
                    "SOLVED" if final_result.sat else "INCONSISTENT"
                )
                return trace

    def _classify_consistent(self, knowledge: KnowledgeBase, cell: str) -> Verdict:
        variable = knowledge.varmap.var(cell)
        criminal_query = self._solve(knowledge, (-variable,))
        if not criminal_query.sat:
            return Verdict.CRIMINAL
        innocent_query = self._solve(knowledge, (variable,))
        if not innocent_query.sat:
            return Verdict.INNOCENT
        return Verdict.UNKNOWN

    def _solve(
        self, knowledge: KnowledgeBase, assumptions: tuple[int, ...]
    ) -> SolveResult:
        return self._solver.solve(
            knowledge.clauses,
            num_vars=knowledge.num_vars,
            assumptions=assumptions,
        )

    @staticmethod
    def _query(cell: str, assumption: str, result: SolveResult) -> SatQuery:
        return SatQuery(
            cell=cell,
            assumption=assumption,
            result=result.status,
            decisions=result.decisions,
            propagations=result.propagations,
            backtracks=result.backtracks,
            runtime=result.runtime,
        )

    @staticmethod
    def _validate_cell(state: PublicState, cell: str) -> None:
        parse_cell(cell, state.size)
        if not any(character.cell == cell for character in state.characters):
            raise ValueError("unknown cell {!r}".format(cell))

    @staticmethod
    def _ordered_cells(state: PublicState) -> list[str]:
        cells = [character.cell for character in state.characters]
        for cell in cells:
            parse_cell(cell, state.size)
        return sorted(cells, key=lambda cell: parse_cell(cell, state.size))
