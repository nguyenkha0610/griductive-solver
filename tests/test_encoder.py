from itertools import product

from griductive.core.models import (
    Character,
    Clue,
    ClueType,
    PublicState,
    Region,
    RegionKind,
    Status,
)
from griductive.logic.cnf_encoder import CNFEncoder
from griductive.logic.evaluator import evaluate_clue
from griductive.logic.variables import VariableMap
from griductive.solver.dpll import DPLLSolver


def test_encoder_matches_semantic_evaluator_for_supported_clues():
    state = PublicState(
        size=2,
        characters=tuple(
            Character(cell, cell, "Unknown")
            for cell in ("A1", "B1", "A2", "B2")
        ),
        revealed_clues=(),
        proved={},
    )
    clues = [
        Clue("fact", ClueType.FACT, ("A1",), Status.CRIMINAL),
        Clue("same", ClueType.SAME, ("A1", "B1")),
        Clue("different", ClueType.DIFFERENT, ("A1", "B1")),
        Clue("exactly", ClueType.EXACTLY, region=Region(RegionKind.ROW, "1"), k=1),
        Clue("at-least", ClueType.AT_LEAST, region=Region(RegionKind.COL, "A"), k=1),
        Clue("at-most", ClueType.AT_MOST, region=Region(RegionKind.CELLS, cells=("A1", "B2")), k=1),
        Clue(
            "parity",
            ClueType.PARITY,
            region=Region(RegionKind.ROW, "2"),
            extra={"parity": "ODD"},
        ),
        Clue(
            "compare",
            ClueType.COMPARE,
            extra={
                "region_a": {"kind": "ROW", "ref": "1"},
                "region_b": {"kind": "COL", "ref": "A"},
                "operator": ">",
            },
        ),
    ]

    for clue in clues:
        varmap = VariableMap(state)
        encoder = CNFEncoder(varmap, state.size)
        clauses = encoder.encode_clue(clue)
        solver = DPLLSolver(num_vars=varmap.num_primary + varmap.num_aux)
        for values in product((False, True), repeat=4):
            assignment = {
                cell: Status.CRIMINAL if value else Status.INNOCENT
                for cell, value in zip(varmap.cell_to_var, values)
            }
            assumptions = [
                variable if assignment[cell] == Status.CRIMINAL else -variable
                for cell, variable in varmap.cell_to_var.items()
            ]
            assert solver.solve(
                clauses,
                num_vars=varmap.num_primary + varmap.num_aux,
                assumptions=assumptions,
            ).sat == evaluate_clue(clue, assignment, state.size), clue.id


def test_sequential_cardinality_encodings_cover_all_bounds():
    state = PublicState(
        size=2,
        characters=tuple(
            Character(cell, cell, "Unknown")
            for cell in ("A1", "B1", "A2", "B2")
        ),
        revealed_clues=(),
        proved={},
    )
    varmap = VariableMap(state)
    encoder = CNFEncoder(varmap, state.size)
    literals = [varmap.var(cell) for cell in ("A1", "B1", "A2", "B2")]

    for k in range(len(literals) + 1):
        encodings = (
            (encoder.encode_at_most(literals, k), lambda count: count <= k),
            (encoder.encode_at_least(literals, k), lambda count: count >= k),
            (encoder.encode_exactly(literals, k), lambda count: count == k),
        )
        for clauses, accepts in encodings:
            solver = DPLLSolver(num_vars=varmap.num_primary + varmap.num_aux)
            for values in product((False, True), repeat=len(literals)):
                assumptions = [
                    literal if value else -literal
                    for literal, value in zip(literals, values)
                ]
                assert solver.solve(
                    clauses,
                    num_vars=varmap.num_primary + varmap.num_aux,
                    assumptions=assumptions,
                ).sat == accepts(sum(values))
