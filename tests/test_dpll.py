from itertools import combinations, product

import pytest

from griductive.solver.dpll import DPLLSolver, solve


def brute_force(cnf, num_vars):
    """Independent truth-table oracle used only by these tests."""
    for values in product((False, True), repeat=num_vars):
        if all(
            any(values[abs(literal) - 1] == (literal > 0) for literal in clause)
            for clause in cnf
        ):
            return True
    return False


def is_satisfied(cnf, model):
    return all(
        any(model[abs(literal)] == (literal > 0) for literal in clause)
        for clause in cnf
    )


def test_sat_simple_and_complete_model():
    cnf = [[1], [2], [-2, 3]]
    result = solve(cnf, 4)

    assert result.status == "SAT"
    assert result.sat
    assert set(result.assignment) == {1, 2, 3, 4}
    assert is_satisfied(cnf, result.model)
    assert result.decisions == 0
    assert result.propagations == 3


def test_unit_propagation_chain():
    result = solve([[1], [-1, 2], [-2, 3]], 3)

    assert result.sat
    assert result.model == {1: True, 2: True, 3: True}
    assert result.propagations == 3
    assert result.decisions == 0


def test_sat_requires_branching():
    cnf = [[1, 2], [-1, 2]]

    result = solve(cnf, 2)

    assert result.sat
    assert is_satisfied(cnf, result.model)
    assert result.decisions >= 1


def test_failed_first_branch_backtracks_to_sat():
    cnf = [[-1, 2], [-1, -2], [1, 2]]

    result = solve(cnf, 2)

    assert result.sat
    assert result.model == {1: False, 2: True}
    assert result.decisions == 2
    assert result.propagations == 2
    assert result.backtracks == 1


def test_unsat_formula():
    assert not solve([[1], [-1]], 1).sat
    assert solve([[1], [-1]], 1).model is None


def test_contradictory_unit_clauses():
    result = solve([[1], [-1]], 1)

    assert result.status == "UNSAT"
    assert result.assignment is None


def test_empty_clause_is_unsat():
    result = solve([[1], []], 1)

    assert not result.sat
    assert result.model is None


def test_empty_cnf_is_sat_and_completes_declared_variables():
    result = solve([], 3)

    assert result.sat
    assert result.model == {1: False, 2: False, 3: False}
    assert result.decisions == result.propagations == result.backtracks == 0


def test_tautology_and_duplicate_literals_are_handled_without_mutation():
    cnf = [[1, -1, 2], [2, 2], [-3, -3]]
    original = [clause.copy() for clause in cnf]

    result = solve(cnf, 3)

    assert result.sat
    assert is_satisfied(cnf, result.model)
    assert cnf == original


def test_deterministic_result_and_trace():
    cnf = [[-1, 2], [-1, -2], [1, 2]]
    solver = DPLLSolver(num_vars=2, trace=True)

    first = solver.solve(cnf)
    second = solver.solve(cnf)

    assert first.status == second.status
    assert first.model == second.model
    assert first.trace == second.trace
    assert any(event.startswith("BACKTRACK:") for event in first.trace)
    assert first.runtime >= 0


def test_assumptions_are_temporary_and_do_not_mutate_cnf():
    cnf = [[1, 2], [-1, 2]]
    original = [clause.copy() for clause in cnf]
    solver = DPLLSolver()

    assert solver.solve(cnf, num_vars=2, assumptions=[-2]).status == "UNSAT"
    assert solver.solve(cnf, num_vars=2).status == "SAT"
    assert cnf == original


def test_contradictory_assumptions_return_unsat():
    result = DPLLSolver().solve([[1, 2]], assumptions=[1, -1])

    assert result.status == "UNSAT"
    assert result.model is None


def test_invalid_formula_inputs_raise_value_error():
    with pytest.raises(ValueError):
        solve([[0]], 1)
    with pytest.raises(ValueError):
        solve([[2]], 1)
    with pytest.raises(ValueError):
        solve([[True]], 1)
    with pytest.raises(ValueError):
        solve([[1]], -1)


def test_matches_brute_force_for_small_cnf_formulas():
    candidate_clauses = [
        [],
        [1],
        [-1],
        [2],
        [-2],
        [1, 2],
        [1, -2],
        [-1, 2],
        [-1, -2],
        [1, -1],
        [2, -2],
    ]
    formulas = [()]
    for count in range(1, 4):
        formulas.extend(combinations(candidate_clauses, count))

    for formula in formulas:
        cnf = [clause.copy() for clause in formula]
        assert solve(cnf, 2).sat == brute_force(cnf, 2), cnf


def test_runtime_is_measured():
    result = solve([[1]], 1)

    assert result.runtime >= 0
    assert result.stats.runtime == result.runtime
