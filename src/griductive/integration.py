"""Phần 5 (Integrator): glue code nối Engine - Agent - Encoder - DPLL."""
from .core.engine import GameEngine
from .agent.deductive_agent import DeductiveAgent


def solve_file(path: str):
    engine = GameEngine.from_file(path)
    trace = DeductiveAgent().auto_solve(engine)
    print(f"Terminal: {trace.terminal}, steps: {len(trace.steps)}")
    for step in trace.steps:
        clues = ", ".join(step.active_clue_ids) or "(none)"
        print(f"Step {step.step}: active clues [{clues}]")
        for query in step.queries:
            target = f" {query.cell}" if query.cell else ""
            print(
                f"  SAT{target} {query.assumption}: {query.result} "
                f"(decisions={query.decisions}, propagations={query.propagations}, "
                f"backtracks={query.backtracks}, runtime={query.runtime:.6f}s)"
            )
        if step.cell and step.verdict:
            print(
                f"  Inferred {step.cell} = {step.verdict.value}; "
                f"revealed {step.revealed_clue_id}"
            )
    return trace
