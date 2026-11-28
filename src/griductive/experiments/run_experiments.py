"""Phần 5: chạy agent trên toàn bộ puzzles/, ghi results/results.csv.
KHÔNG bỏ các case fail/timeout."""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from time import perf_counter

from ..agent.deductive_agent import DeductiveAgent
from ..agent.uniqueness import count_solutions
from ..core.engine import GameEngine
from ..core.puzzle_io import load_puzzle
from ..logic.cnf_encoder import build_kb

ROOT = Path(__file__).resolve().parents[3]
FIELDS = [
    "puzzle",
    "size",
    "primary_vars",
    "aux_vars",
    "clauses",
    "sat_calls",
    "decisions",
    "propagations",
    "backtracks",
    "deduction_steps",
    "runtime_s",
    "status",
]  # status: SOLVED/STUCK/INCONSISTENT/TIMEOUT/ERROR

COMPARISON_FIELDS = ["strategy", "solutions"] + FIELDS

STRATEGIES: tuple[tuple[str, bool, str], ...] = (
    ("baseline", False, "min_var"),
    ("pure_literal", True, "min_var"),
    ("jw_heuristic", False, "jw"),
)


def evaluate_puzzle(
    puzzle_path: str | Path,
    pure_literal: bool = False,
    heuristic: str = "min_var",
    check_unique: bool = False,
) -> dict:
    """Run DeductiveAgent on one puzzle and collect metrics."""
    path = Path(puzzle_path)
    puzzle = load_puzzle(path)
    engine = GameEngine(puzzle)
    agent = DeductiveAgent(pure_literal=pure_literal, heuristic=heuristic)

    started = perf_counter()
    trace = agent.auto_solve(engine)
    runtime_s = perf_counter() - started

    kb = build_kb(engine.public_state())
    sat_calls = sum(len(step.queries) for step in trace.steps)
    decisions = sum(q.decisions for step in trace.steps for q in step.queries)
    propagations = sum(q.propagations for step in trace.steps for q in step.queries)
    backtracks = sum(q.backtracks for step in trace.steps for q in step.queries)

    try:
        rel = path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        rel = path.name

    row = {
        "puzzle": rel,
        "size": puzzle.size,
        "primary_vars": kb.stats["primary_vars"],
        "aux_vars": kb.stats["aux_vars"],
        "clauses": kb.stats["clauses"],
        "sat_calls": sat_calls,
        "decisions": decisions,
        "propagations": propagations,
        "backtracks": backtracks,
        "deduction_steps": len(trace.steps),
        "runtime_s": round(runtime_s, 6),
        "status": trace.terminal or "ERROR",
    }
    if check_unique:
        row["solutions"] = count_solutions(
            list(puzzle.clues.values()), engine.public_state(), limit=2
        )
    return row


def _run_subprocess(
    puzzle_path: Path,
    timeout: float,
    pure_literal: bool = False,
    heuristic: str = "min_var",
    check_unique: bool = False,
) -> dict:
    cmd = [
        sys.executable,
        "-m",
        "griductive.experiments.run_experiments",
        "--single",
        str(puzzle_path),
        "--heuristic",
        heuristic,
    ]
    if pure_literal:
        cmd.append("--pure-literal")
    if check_unique:
        cmd.append("--check-unique")

    try:
        rel = puzzle_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        rel = puzzle_path.name

    env = dict(os.environ)
    src_path = str(ROOT / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing}" if existing else src_path

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        row = _fallback_metadata(puzzle_path, rel, timeout, "TIMEOUT")
        if check_unique:
            row["solutions"] = ""
        return row

    if completed.returncode != 0 or not completed.stdout.strip():
        row = _fallback_metadata(puzzle_path, rel, 0.0, "ERROR")
        if check_unique:
            row["solutions"] = ""
        return row

    last_line = completed.stdout.strip().splitlines()[-1]
    return json.loads(last_line)


def _fallback_metadata(
    puzzle_path: Path, rel: str, runtime_s: float, status: str
) -> dict:
    size = 0
    primary = 0
    aux = 0
    clauses = 0
    try:
        puzzle = load_puzzle(puzzle_path)
        engine = GameEngine(puzzle)
        kb = build_kb(engine.public_state())
        size = puzzle.size
        primary = kb.stats["primary_vars"]
        aux = kb.stats["aux_vars"]
        clauses = kb.stats["clauses"]
    except Exception:
        pass
    return {
        "puzzle": rel,
        "size": size,
        "primary_vars": primary,
        "aux_vars": aux,
        "clauses": clauses,
        "sat_calls": 0,
        "decisions": 0,
        "propagations": 0,
        "backtracks": 0,
        "deduction_steps": 0,
        "runtime_s": round(runtime_s, 6),
        "status": status,
    }


def run_all(
    timeout: float = 60.0,
    puzzles_dir: Path | None = None,
    out_path: Path | None = None,
    comparison_path: Path | None = None,
) -> list[dict]:
    """Run experiments on all puzzles and write results CSVs (never skipping failures/timeouts)."""
    p_dir = puzzles_dir or (ROOT / "puzzles")
    out = out_path or (ROOT / "results" / "results.csv")
    comp_out = comparison_path or (ROOT / "results" / "comparison.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    comp_out.parent.mkdir(parents=True, exist_ok=True)

    puzzle_files = sorted(p_dir.rglob("*.json"))
    baseline_rows: list[dict] = []
    comparison_rows: list[dict] = []

    for puzzle_path in puzzle_files:
        for strategy_name, pure_lit, heuristic in STRATEGIES:
            row = _run_subprocess(
                puzzle_path,
                timeout=timeout,
                pure_literal=pure_lit,
                heuristic=heuristic,
                check_unique=(strategy_name == "baseline"),
            )
            if strategy_name == "baseline":
                baseline_rows.append({k: row[k] for k in FIELDS})
                comp_row = {"strategy": strategy_name, **row}
            else:
                sol_val = next(
                    (r.get("solutions", "") for r in comparison_rows
                     if r["puzzle"] == row["puzzle"] and r["strategy"] == "baseline"),
                    "",
                )
                comp_row = {"strategy": strategy_name, "solutions": sol_val, **row}
            comparison_rows.append({k: comp_row.get(k, "") for k in COMPARISON_FIELDS})

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(baseline_rows)

    with open(comp_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COMPARISON_FIELDS)
        writer.writeheader()
        writer.writerows(comparison_rows)

    print(f"Wrote {out} ({len(baseline_rows)} puzzles)")
    print(f"Wrote {comp_out} ({len(comparison_rows)} runs)")
    return baseline_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Griductive experiments")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--single", type=str, default=None)
    parser.add_argument("--pure-literal", action="store_true")
    parser.add_argument("--heuristic", type=str, default="min_var")
    parser.add_argument("--check-unique", action="store_true")
    args = parser.parse_args()

    if args.single:
        row = evaluate_puzzle(
            args.single,
            pure_literal=args.pure_literal,
            heuristic=args.heuristic,
            check_unique=args.check_unique,
        )
        print(json.dumps(row))
    else:
        run_all(timeout=args.timeout)


if __name__ == "__main__":
    main()
