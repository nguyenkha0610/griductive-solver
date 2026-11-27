"""Count distinct primary-variable models of a complete puzzle clue set."""
from __future__ import annotations

from collections.abc import Sequence

from ..core.models import Character, Clue, PublicState
from ..logic.cnf_encoder import CNFEncoder
from ..logic.variables import VariableMap
from ..solver.dpll import DPLLSolver


def count_solutions(
    all_clues: list[Clue],
    characters_state: PublicState | Sequence[Character],
    limit: int = 2,
) -> int:
    """Return the number of models, capped at ``limit`` (2 means "2 or more").

    Auxiliary-variable assignments are not distinct puzzle solutions: each
    discovered model is blocked only on the primary character variables.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    state = _as_public_state(characters_state)
    varmap = VariableMap(state)
    encoder = CNFEncoder(varmap, state.size)
    clauses = [
        clause
        for clue in all_clues
        for clause in encoder.encode_clue(clue)
    ]
    solver = DPLLSolver(num_vars=varmap.num_primary + varmap.num_aux)
    solution_count = 0
    while solution_count < limit:
        result = solver.solve(
            clauses,
            num_vars=varmap.num_primary + varmap.num_aux,
        )
        if not result.sat:
            break
        solution_count += 1
        model = result.model
        if model is None:
            raise RuntimeError("SAT solver returned SAT without a model")
        clauses.append([
            -variable if model[variable] else variable
            for variable in range(1, varmap.num_primary + 1)
        ])
    return solution_count


def check_uniqueness(
    all_clues: list[Clue],
    characters_state: PublicState | Sequence[Character],
) -> bool:
    """Return whether the complete clue set has exactly one solution."""
    return count_solutions(all_clues, characters_state, limit=2) == 1


def _as_public_state(
    characters_state: PublicState | Sequence[Character],
) -> PublicState:
    if isinstance(characters_state, PublicState):
        return PublicState(
            size=characters_state.size,
            characters=characters_state.characters,
            revealed_clues=(),
            proved={},
        )
    characters = tuple(characters_state)
    if not characters:
        raise ValueError("at least one character is required")
    column_count = max(
        _column_number(character.cell) for character in characters
    )
    row_count = max(int(character.cell[_column_end(character.cell):]) for character in characters)
    size = max(column_count, row_count)
    return PublicState(
        size=size,
        characters=characters,
        revealed_clues=(),
        proved={},
    )


def _column_end(cell: str) -> int:
    index = 0
    while index < len(cell) and cell[index].isalpha():
        index += 1
    if index == 0 or index == len(cell):
        raise ValueError("invalid cell id {!r}".format(cell))
    return index


def _column_number(cell: str) -> int:
    end = _column_end(cell)
    column = 0
    for letter in cell[:end]:
        if not letter.isupper() or not letter.isascii():
            raise ValueError("invalid cell id {!r}".format(cell))
        column = column * 26 + ord(letter) - ord("A") + 1
    return column
