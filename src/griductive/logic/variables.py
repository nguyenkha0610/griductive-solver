"""Ánh xạ deterministic cell -> primary variable C_i (Phần 2).
Quy ước: DIMACS-style, biến là số nguyên dương 1..N; literal âm = phủ định.
Primary: 1..N (N = số nhân vật). Auxiliary: > N, tách biệt hoàn toàn."""
from __future__ import annotations
from ..core.models import PublicState


class VariableMap:
    def __init__(self, state: PublicState):
        # characters đã sort theo tên -> thứ tự biến cố định
        self.cell_to_var = {c.cell: i + 1 for i, c in enumerate(state.characters)}
        self.var_to_cell = {v: c for c, v in self.cell_to_var.items()}
        self.num_primary = len(self.cell_to_var)
        self._next_aux = self.num_primary + 1
        self.num_aux = 0

    def var(self, cell: str) -> int:
        return self.cell_to_var[cell]

    def new_aux(self) -> int:
        v = self._next_aux
        self._next_aux += 1
        self.num_aux += 1
        return v
