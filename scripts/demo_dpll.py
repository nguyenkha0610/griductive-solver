"""Terminal demonstration of SAT discovery and an UNSAT search trace."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from griductive.solver.dpll import DPLLSolver


def satisfies(cnf, assignment):
    """Return whether a complete assignment satisfies every clause."""
    return all(
        any(assignment[abs(literal)] == (literal > 0) for literal in clause)
        for clause in cnf
    )


def show_case(title, cnf, num_vars):
    print("\n" + "=" * 68)
    print(title)
    print("CNF:", cnf)
    result = DPLLSolver(num_vars=num_vars, trace=True).solve(cnf)
    for event in result.trace:
        print("  " + event)
    print("Status:", result.status)
    if result.sat:
        print("Assignment:", result.assignment)
        print("Assignment satisfies CNF:", satisfies(cnf, result.assignment))
        if not satisfies(cnf, result.assignment):
            raise AssertionError("DPLL returned an invalid satisfying assignment")
    else:
        print("Assignment: none (UNSAT)")
    print(
        "Decisions: {}; propagations: {}; backtracks: {}; runtime: {:.6f}s".format(
            result.decisions,
            result.propagations,
            result.backtracks,
            result.runtime,
        )
    )


def main():
    """Run one SAT and one UNSAT example."""
    show_case(
        "DEMO 1 - SAT with a failed first branch",
        [[-1, 2], [-1, -2], [1, 2]],
        2,
    )
    show_case(
        "DEMO 2 - UNSAT with propagation, branching, and backtracking",
        [[1, 2], [1, -2], [-1, 2], [-1, -2]],
        2,
    )


if __name__ == "__main__":
    main()
