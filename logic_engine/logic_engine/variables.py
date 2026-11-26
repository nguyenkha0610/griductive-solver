"""Quản lý biến Boolean: biến chính (mỗi ô trên lưới) và biến phụ (encoding)."""


class VariablePool:
    def __init__(self, n):
        self.n = n
        self._primary = {}          # (r, c) -> var id
        for r in range(n):
            for c in range(n):
                self._primary[(r, c)] = r * n + c + 1   # 1..N*N
        self._next = n * n + 1
        self.num_aux = 0

    @property
    def num_primary(self):
        return self.n * self.n

    def var(self, cell):
        """Biến chính của ô (r, c). True = nhân vật ở ô đó mang trạng thái 'dương'."""
        return self._primary[cell]

    def cell_of(self, var):
        for cell, v in self._primary.items():
            if v == var:
                return cell
        return None

    def new_aux(self):
        v = self._next
        self._next += 1
        self.num_aux += 1
        return v
