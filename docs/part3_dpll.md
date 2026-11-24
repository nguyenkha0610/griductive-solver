# Part 3: DPLL SAT Solver

## 1. Introduction

The Davis-Putnam-Logemann-Loveland (DPLL) procedure is a complete,
backtracking search algorithm for deciding the satisfiability of propositional
formulas in conjunctive normal form (CNF). It repeatedly simplifies a formula
under a partial assignment, detects contradictions, and branches on an
unassigned variable when deterministic propagation is insufficient.

Griductive Solver uses propositional variables to represent the status of
characters and converts revealed clues and already-proved facts into CNF. DPLL
answers whether that public knowledge is consistent and whether a temporary
candidate assumption is possible. It receives only the encoded knowledge base;
it does not read the engine's hidden solution or unrevealed clues.

## 2. CNF Representation

The solver uses the DIMACS-style representation produced by the Part 2
encoder:

* A Boolean variable is a positive integer (`1`, `2`, ...).
* A positive literal (`v`) means that variable `v` is true; a negative
  literal (`-v`) means it is false.
* A clause is a sequence of literals interpreted as disjunction.
* A CNF formula is a sequence of clauses interpreted as conjunction.

For example:

```python
cnf = [[1, 2], [-1, 3], [-2, -3]]
```

represents `(x1 OR x2) AND (NOT x1 OR x3) AND (NOT x2 OR NOT x3)`.
An empty CNF is true, while a CNF containing an empty clause is false.
Repeated literals are harmless; a clause containing both `v` and `-v` is a
tautology and is ignored during search. The solver validates that every literal
is a non-zero integer within the declared variable range and does not modify
the caller's CNF.

## 3. Algorithm Components

### Unit propagation

For each clause, the solver skips it if an assigned literal makes it true.
Otherwise it collects unassigned literals. A clause with exactly one such
literal forces that literal to true. The formula is scanned again after each
forced assignment, continuing until no unit clause remains. The propagations
counter includes each new assignment inferred this way, including in failed
branches; assumptions and branch decisions are not propagations.

### Conflict detection

A clause with no true literal and no unassigned literal is false under the
current assignment, so the search immediately returns failure for that branch.
Opposite unit requirements are detected when the earlier unit assignment makes
the other clause false. Contradictory assumptions likewise produce UNSAT
without entering the search.

### Deterministic variable selection

After propagation, the solver collects unassigned variables appearing in
clauses that are not already satisfied, then chooses the smallest variable
number. It never branches on an assigned variable or on variables occurring
only in satisfied clauses.

### Recursive branching and backtracking

The selected variable is first assigned `True`, then `False` if the first
branch fails. Each child receives a copy of the current assignment; failed
branch assignments therefore cannot leak into a sibling. A satisfying branch
returns immediately. If both values fail, the current recursive call returns
UNSAT.

### Statistics

`decisions` counts each attempted branch assignment (including the second
polarity). `propagations` counts new unit-derived assignments. `backtracks`
counts each failed branch assignment that is abandoned. `runtime` is elapsed
wall-clock time measured with `time.perf_counter()`. The returned model, when
SAT, includes every variable from `1` through `num_vars`; variables not needed
to satisfy the formula are deterministically completed as `False`.

## 4. Pseudocode

The following pseudocode matches the implementation, including the order of
the two branch values and the statistics:

```text
SOLVE(CNF, num_vars, assumptions):
    validate literals and variable range
    normalize clauses by removing duplicate literals and tautologies
    assignment := assignments from assumptions
    if assumptions conflict: return UNSAT
    model := SEARCH(assignment)
    return SAT(model) if model exists, otherwise UNSAT

SEARCH(assignment):
    repeat:
        find the first clause not already true
        if it has no unassigned literals: return failure (conflict)
        if it has exactly one unassigned literal:
            assign that literal; increment propagations
        else:
            stop propagation

    variables := unassigned variables in clauses not already true
    if variables is empty:
        assign False to each undeclared value in 1..num_vars
        return the completed assignment

    variable := smallest variable in variables
    for value in [True, False]:
        increment decisions
        child := a copy of assignment with variable := value
        model := SEARCH(child)
        if model exists: return model
        increment backtracks
    return failure
```

## 5. Worked Example

Consider:

```text
CNF = [[-1, 2], [-1, -2], [1, 2]]
       (NOT x1 OR x2) AND (NOT x1 OR NOT x2) AND (x1 OR x2)
```

There are no initial unit clauses. The deterministic selector chooses `x1`.

1. The first branch assigns `x1 = True`.
2. The first clause becomes the unit clause `[2]`; propagation assigns
   `x2 = True`.
3. The second clause `[-1, -2]` is now false, so this branch conflicts.
4. The solver abandons that branch and tries `x1 = False`.
5. The third clause `[1, 2]` becomes unit, so propagation assigns `x2 = True`.
   The remaining clauses are satisfied.
6. The result is SAT with `{1: False, 2: True}`.

This example is executed by `scripts/demo_dpll.py`. With the defined counters,
it records two decisions, two propagations, and one backtrack. Runtime depends
on the execution environment.

## 6. Complexity Analysis

For `n` variables, DPLL has a worst-case exponential search tree with up to
`O(2^n)` assignments. A direct scan of all literals in the CNF at each search
node yields an upper bound of `O(2^n * L)`, where `L` is the total number of
literal occurrences. Recursion depth is at most `n`. Because each recursive
branch copies its assignment and keeps its local candidate-variable set,
worst-case auxiliary search space is `O(n^2)`; the stored formula requires
`O(L)` additional space.

For small Griductive puzzles, unit propagation often fixes many variables
before branching, so practical search can be much smaller than the worst case.
This implementation favors clarity and deterministic behavior over advanced
performance optimizations.

## 7. Experimental Results

The repository's test suite includes ten required scenario categories and a
truth-table oracle comparison over all two-variable CNFs formed from up to
three selected clauses. The demo cases also provide concrete solver counters:

| Case | Expected status | Decisions | Propagations | Backtracks | Runtime |
|---|---:|---:|---:|---:|---:|
| Worked SAT example above | SAT | 2 | 2 | 1 | 0.000047 s |
| Four-clause two-variable contradiction in the demo | UNSAT | 2 | 2 | 2 | 0.000033 s |

The table's deterministic counters correspond to the code's documented
definitions. The runtime values above are from one execution in the current
environment; they vary with hardware and system load. The demo measures and
prints the actual runtime for each run.

## 8. Limitations

This educational implementation uses chronological backtracking, repeatedly
scans the clauses, and selects the smallest eligible variable. It does not
perform pure-literal elimination, watched-literal propagation, conflict
learning, restarts, or advanced branching heuristics such as VSIDS. These are
potential future improvements if larger puzzle encodings make search costly.

## 9. Integration API

The solver supports both the Part 3 function contract and a reusable class:

```python
from griductive.solver.dpll import DPLLSolver, solve

result = solve(kb.clauses, kb.num_vars)
# or, when the number of variables can be inferred:
result = DPLLSolver().solve(cnf)

if result.status == "SAT":
    model = result.assignment
```

For Part 4, test a candidate status by adding a temporary literal assumption.
If `variable` is the primary-variable id for a cell, use `variable` to test
`True` and `-variable` to test `False`:

```python
candidate = solve(kb.clauses, kb.num_vars, assumptions=[variable])
opposite = solve(kb.clauses, kb.num_vars, assumptions=[-variable])
```

The assumptions are not appended to or otherwise written into
`kb.clauses`. Part 4 can classify a candidate using the SAT/UNSAT outcomes of
these two independent calls. The encoder must continue to construct its
knowledge base only from the supplied `PublicState`; DPLL receives no hidden
solution data.
