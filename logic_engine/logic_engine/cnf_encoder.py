"""Chuyển Clue sang CNF + Knowledge Base."""
from clues import ClueType, validate
from variables import VariablePool


def _at_most(pool, lits, k):
    """Sinz sequential counter: tổng các literal True <= k."""
    n = len(lits)
    if k >= n:
        return []
    if k == 0:
        return [[-x] for x in lits]
    s = [[pool.new_aux() for _ in range(k)] for _ in range(n - 1)]
    cl = [[-lits[0], s[0][0]]]
    cl += [[-s[0][j]] for j in range(1, k)]
    for i in range(1, n - 1):
        cl.append([-lits[i], s[i][0]])
        cl.append([-s[i - 1][0], s[i][0]])
        for j in range(1, k):
            cl.append([-lits[i], -s[i - 1][j - 1], s[i][j]])
            cl.append([-s[i - 1][j], s[i][j]])
        cl.append([-lits[i], -s[i - 1][k - 1]])
    cl.append([-lits[n - 1], -s[n - 2][k - 1]])
    return cl


def _at_least(pool, lits, k):
    # sum(x) >= k  <=>  sum(not x) <= n - k
    return _at_most(pool, [-x for x in lits], len(lits) - k)


def _parity(pool, lits, odd):
    """Chuỗi XOR bằng biến phụ: t_i = t_{i-1} xor x_i; ép t_n theo parity."""
    t = lits[0]
    for x in lits[1:]:
        y = pool.new_aux()
        cl_xor = [[-y, t, x], [-y, -t, -x], [y, -t, x], [y, t, -x]]
        yield_cl = cl_xor
        for c in yield_cl:
            _parity.buf.append(c)
        t = y
    _parity.buf.append([t] if odd else [-t])


_parity.buf = []


def encode_clue(clue, pool):
    cells = validate(clue, pool.n)
    lits = [pool.var(c) for c in cells]
    t, v = clue.type, clue.value
    if t == ClueType.FACT:
        return [[lits[0] if v else -lits[0]]]
    if t == ClueType.SAME:
        return [[-a, b] for a in lits for b in lits if a != b]
    if t == ClueType.DIFFERENT:
        return [list(lits), [-x for x in lits]]
    if t == ClueType.EXACTLY:
        return _at_least(pool, lits, v) + _at_most(pool, lits, v)
    if t == ClueType.AT_LEAST:
        return _at_least(pool, lits, v)
    if t == ClueType.AT_MOST:
        return _at_most(pool, lits, v)
    if t == ClueType.BETWEEN:
        return _at_least(pool, lits, v[0]) + _at_most(pool, lits, v[1])
    if t == ClueType.PARITY:
        _parity.buf = []
        _parity(pool, lits, bool(v))
        return list(_parity.buf)
    raise ValueError(t)


class KnowledgeBase:
    def __init__(self, n):
        self.pool = VariablePool(n)
        self.clauses = []

    def add_clause(self, clause):
        self.clauses.append(list(clause))

    def add_clue(self, clue):
        cl = encode_clue(clue, self.pool)
        self.clauses.extend(cl)
        return cl

    def add_verdict(self, cell, value):
        """Thêm kết luận đã chứng minh dưới dạng unit clause."""
        v = self.pool.var(cell)
        self.clauses.append([v if value else -v])
