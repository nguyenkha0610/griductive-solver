"""Kiểm tra chéo: CNF (tồn tại biến phụ thỏa) <=> đánh giá ngữ nghĩa, trên lưới 3x3."""
import itertools, random
from regions import row, col, neighbors, custom
from clues import Clue, ClueType as T
from cnf_encoder import KnowledgeBase
from semantic_eval import evaluate
from stats import collect_stats


def dpll(clauses, assign):
    clauses = [c for c in clauses]
    while True:
        unit, new = None, []
        for c in clauses:
            if any(assign.get(abs(l)) == (l > 0) for l in c):
                continue
            rest = [l for l in c if abs(l) not in assign]
            if not rest:
                return False
            if len(rest) == 1:
                unit = rest[0]
            new.append(rest)
        if unit is None:
            break
        assign = {**assign, abs(unit): unit > 0}
        clauses = new
    if not new:
        return True
    v = abs(new[0][0])
    return dpll(new, {**assign, v: True}) or dpll(new, {**assign, v: False})


def main():
    n = 3
    regions = [row(1), col(0), neighbors(1, 1), neighbors(0, 0, False), custom([(0, 0), (2, 2), (1, 2)])]
    clues = []
    for reg in regions:
        clues += [Clue(T.SAME, reg), Clue(T.DIFFERENT, reg), Clue(T.PARITY, reg, 0), Clue(T.PARITY, reg, 1)]
        for k in (0, 1, 2):
            clues += [Clue(T.EXACTLY, reg, k), Clue(T.AT_LEAST, reg, k), Clue(T.AT_MOST, reg, k)]
        clues.append(Clue(T.BETWEEN, reg, (1, 2)))
    clues += [Clue(T.FACT, custom([(1, 1)]), True), Clue(T.FACT, custom([(2, 0)]), False)]
    bad = 0
    cells = [(r, c) for r in range(n) for c in range(n)]
    states = random.Random(0).sample(list(itertools.product([False, True], repeat=9)), 60)
    for clue in clues:
        kb = KnowledgeBase(n)
        kb.add_clue(clue)
        for st in states:
            a = dict(zip(cells, st))
            prim = {kb.pool.var(c): a[c] for c in cells}
            if dpll(kb.clauses, prim) != evaluate(clue, a, n):
                bad += 1
                print("MISMATCH", clue)
                break
    print("clues tested:", len(clues), "mismatches:", bad)
    kb = KnowledgeBase(n)
    kb.add_clue(Clue(T.EXACTLY, row(0), 2))
    kb.add_verdict((0, 0), True)
    print(collect_stats(kb))


if __name__ == "__main__":
    main()
