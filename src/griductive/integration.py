"""Phần 5 (Integrator): glue code nối Engine - Agent - Encoder - DPLL."""
from .core.engine import GameEngine
from .agent.deductive_agent import DeductiveAgent


def solve_file(path: str):
    engine = GameEngine.from_file(path)
    trace = DeductiveAgent().auto_solve(engine)
    print(f"Terminal: {trace.terminal}, steps: {len(trace.steps)}")
    return trace
