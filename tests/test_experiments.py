from itertools import combinations
from pathlib import Path

from griductive.agent.deductive_agent import DeductiveAgent
from griductive.core.models import Clue, ClueType, Region, RegionKind
from griductive.core.puzzle_io import load_puzzle
from griductive.experiments.plots import make_plots
from griductive.experiments.run_experiments import (
    FIELDS,
    evaluate_puzzle,
    run_all,
)
from griductive.gui.clue_text import clue_to_text
from griductive.logic.evaluator import evaluate_clue
from griductive.solver.dpll import DPLLSolver


def _brute_force(cnf, num_vars):
    from itertools import product
    for values in product((False, True), repeat=num_vars):
        if all(
            any(values[abs(lit) - 1] == (lit > 0) for lit in clause)
            for clause in cnf
        ):
            return True
    return False


def test_optional_dpll_modes_match_brute_force():
    candidate_clauses = [
        [], [1], [-1], [2], [-2],
        [1, 2], [1, -2], [-1, 2], [-1, -2],
    ]
    formulas = [()] + [c for k in range(1, 4) for c in combinations(candidate_clauses, k)]
    solvers = [
        DPLLSolver(num_vars=2, pure_literal=True),
        DPLLSolver(num_vars=2, heuristic="jw"),
        DPLLSolver(num_vars=2, pure_literal=True, heuristic="jw"),
    ]
    for formula in formulas:
        cnf = [list(c) for c in formula]
        expected = _brute_force(cnf, 2)
        for solver in solvers:
            assert solver.solve(cnf).sat == expected


def test_clue_text_renders_valid_compare():
    c = Clue(
        "clue_A1",
        ClueType.COMPARE,
        extra={
            "region_a": Region(RegionKind.COL, "C"),
            "region_b": Region(RegionKind.ROW, "2"),
            "operator": ">",
        },
    )
    text = clue_to_text(c)
    assert "cột C" in text and "nhiều hơn" in text and "hàng 2" in text


def test_all_puzzles_have_valid_structure_and_true_clues():
    puzzles_dir = Path("puzzles")
    files = sorted(puzzles_dir.rglob("*.json"))
    assert len(files) >= 6
    for path in files:
        puzzle = load_puzzle(path)
        for cell, clue in puzzle.clues.items():
            assert evaluate_clue(clue, puzzle.solution, puzzle.size), f"{path} {cell}"


def test_evaluate_puzzle_and_run_all_and_plots(tmp_path):
    p_dir = tmp_path / "puzzles"
    p_dir.mkdir()
    # Copy 2x2 solvable and 3x3 stuck puzzle
    (p_dir / "agent_chain.json").write_text(
        Path("puzzles/2x2/agent_chain.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (p_dir / "example_3x3.json").write_text(
        Path("puzzles/3x3/example_3x3.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    row = evaluate_puzzle(p_dir / "agent_chain.json", check_unique=True)
    assert row["status"] == "SOLVED"
    assert row["solutions"] == 1
    assert row["deduction_steps"] == 3

    out_csv = tmp_path / "results.csv"
    comp_csv = tmp_path / "comparison.csv"
    fig_dir = tmp_path / "figures"

    rows = run_all(
        timeout=30.0,
        puzzles_dir=p_dir,
        out_path=out_csv,
        comparison_path=comp_csv,
    )
    assert len(rows) == 2
    statuses = {Path(r["puzzle"]).name: r["status"] for r in rows}
    assert statuses["agent_chain.json"] == "SOLVED"
    assert statuses["example_3x3.json"] == "STUCK"
    assert list(rows[0].keys()) == FIELDS

    figs = make_plots(out_csv, comp_csv, fig_dir)
    assert len(figs) == 3
    assert all(f.exists() and f.stat().st_size > 0 for f in figs)
