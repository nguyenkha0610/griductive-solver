"""Phần 5: đọc results/results.csv -> biểu đồ vào docs/figures/."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]


def make_plots(
    results_path: Path | None = None,
    comparison_path: Path | None = None,
    figures_dir: Path | None = None,
) -> list[Path]:
    """Generate experiment figures from results CSV files."""
    res_csv = results_path or (ROOT / "results" / "results.csv")
    comp_csv = comparison_path or (ROOT / "results" / "comparison.csv")
    out_dir = figures_dir or (ROOT / "docs" / "figures")
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(res_csv)
    if df.empty:
        return []

    df = df.copy()
    df["label"] = df["puzzle"].apply(lambda p: Path(str(p)).stem)
    created: list[Path] = []

    # 1. CNF Variables & Clauses per puzzle
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    x = range(len(df))
    w = 0.36
    axes[0].bar([i - w / 2 for i in x], df["primary_vars"], width=w, label="Primary vars", color="#2b6cb0")
    axes[0].bar([i + w / 2 for i in x], df["aux_vars"], width=w, label="Auxiliary vars", color="#ed8936")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(df["label"], rotation=35, ha="right", fontsize=8)
    axes[0].set_ylabel("Count")
    axes[0].set_title("CNF Variables by Puzzle")
    axes[0].legend()
    axes[0].grid(axis="y", alpha=0.3)

    from matplotlib.patches import Patch
    colors = [
        "#2f855a" if s == "SOLVED" else ("#c53030" if s in ("TIMEOUT", "ERROR", "INCONSISTENT") else "#d69e2e")
        for s in df["status"]
    ]
    axes[1].bar(list(x), df["clauses"], color=colors)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(df["label"], rotation=35, ha="right", fontsize=8)
    axes[1].set_ylabel("Clauses")
    axes[1].set_title("Generated CNF Clauses by Puzzle")
    axes[1].legend(
        handles=[
            Patch(facecolor="#2f855a", label="SOLVED"),
            Patch(facecolor="#d69e2e", label="STUCK"),
            Patch(facecolor="#c53030", label="TIMEOUT / ERROR"),
        ],
        fontsize=8,
        loc="upper left",
    )
    axes[1].grid(axis="y", alpha=0.3)

    fig.tight_layout()
    p1 = out_dir / "cnf_size_by_puzzle.png"
    fig.savefig(p1, dpi=180)
    plt.close(fig)
    created.append(p1)

    # 2. Solver search work: SAT calls, decisions, propagations, backtracks
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].bar(list(x), df["sat_calls"], color="#4c51bf")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(df["label"], rotation=35, ha="right", fontsize=8)
    axes[0].set_ylabel("SAT Calls")
    axes[0].set_title("Total SAT Calls per Puzzle")
    axes[0].grid(axis="y", alpha=0.3)

    w2 = 0.28
    axes[1].bar([i - w2 for i in x], df["decisions"], width=w2, label="Decisions", color="#3182ce")
    axes[1].bar(list(x), df["backtracks"], width=w2, label="Backtracks", color="#e53e3e")
    axes[1].bar([i + w2 for i in x], df["propagations"], width=w2, label="Propagations", color="#38a169")
    axes[1].set_yscale("symlog", linthresh=1)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(df["label"], rotation=35, ha="right", fontsize=8)
    axes[1].set_ylabel("Count (symlog scale)")
    axes[1].set_title("DPLL Search Metrics per Puzzle")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.3)

    fig.tight_layout()
    p2 = out_dir / "solver_work_by_puzzle.png"
    fig.savefig(p2, dpi=180)
    plt.close(fig)
    created.append(p2)

    # 3. Runtime & Strategy Comparison (if comparison.csv exists)
    if comp_csv.exists():
        cdf = pd.read_csv(comp_csv)
        if not cdf.empty:
            cdf["label"] = cdf["puzzle"].apply(lambda p: Path(str(p)).stem)
            pivot_rt = cdf.pivot(index="label", columns="strategy", values="runtime_s").reindex(df["label"])
            pivot_dec = cdf.pivot(index="label", columns="strategy", values="decisions").reindex(df["label"])

            fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.5))
            pivot_rt.plot(kind="bar", ax=axes[0], colormap="tab10")
            axes[0].set_ylabel("Runtime (s)")
            axes[0].set_title("Runtime Comparison across DPLL Strategies")
            axes[0].tick_params(axis="x", rotation=35, labelsize=8)
            axes[0].grid(axis="y", alpha=0.3)

            pivot_dec.plot(kind="bar", ax=axes[1], colormap="tab10")
            axes[1].set_yscale("symlog", linthresh=1)
            axes[1].set_ylabel("Decisions (symlog)")
            axes[1].set_title("Branching Decisions Comparison across Strategies")
            axes[1].tick_params(axis="x", rotation=35, labelsize=8)
            axes[1].grid(axis="y", alpha=0.3)

            fig.tight_layout()
            p3 = out_dir / "strategy_comparison.png"
            fig.savefig(p3, dpi=180)
            plt.close(fig)
            created.append(p3)

    return created


if __name__ == "__main__":
    paths = make_plots()
    for path in paths:
        print(f"Saved {path}")
