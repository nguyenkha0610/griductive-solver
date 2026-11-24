# Recording the DPLL Demonstration

Run the demo from the repository root with Python 3:

```powershell
python scripts/demo_dpll.py
```

The script prints the CNF, each propagation/decision/conflict/backtrack event,
the final status, the SAT assignment check, and the measured counters/runtime.
It first runs a SAT case whose `True` branch fails before the `False` branch
succeeds, then an UNSAT four-clause case that fails under both values of the
selected variable.

For a short recording, show the terminal, run the command once, pause on the
SAT assignment and statistics, then scroll through the UNSAT trace and its
final UNSAT result. No GUI or puzzle hidden solution is required.

The automated tests can be run separately with:

```powershell
python -m pytest
```
