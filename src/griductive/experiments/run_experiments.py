"""Phần 5: chạy agent trên toàn bộ puzzles/, ghi results/results.csv.
KHÔNG bỏ các case fail/timeout."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIELDS = ["puzzle", "size", "primary_vars", "aux_vars", "clauses", "sat_calls",
          "decisions", "propagations", "backtracks", "deduction_steps",
          "runtime_s", "status"]   # status: SOLVED/STUCK/TIMEOUT/ERROR


def run_all(timeout: float = 60.0) -> None:
    out = ROOT / "results" / "results.csv"
    rows: list[dict] = []
    for p in sorted((ROOT / "puzzles").rglob("*.json")):
        # TODO: chạy từng puzzle (subprocess + timeout), thu thập metrics
        pass
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out}")
