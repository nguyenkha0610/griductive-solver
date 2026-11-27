from griductive.agent.deductive_agent import DeductiveAgent
from griductive.agent.uniqueness import check_uniqueness, count_solutions
from griductive.core.models import (
    Character,
    Clue,
    ClueType,
    PublicState,
    Region,
    RegionKind,
    Status,
    Verdict,
)


def make_state(clues=(), proved=None):
    return PublicState(
        size=2,
        characters=(
            Character("A1", "Ada", "Judge"),
            Character("B1", "Ben", "Guard"),
        ),
        revealed_clues=tuple(clues),
        proved=proved or {},
    )


def fact(cell, status, clue_id):
    return Clue(
        id=clue_id,
        type=ClueType.FACT,
        targets=(cell,),
        fact_status=status,
    )


def test_classification_uses_both_sat_assumptions():
    agent = DeductiveAgent()
    state = make_state((fact("B1", Status.CRIMINAL, "fact_b1"),))

    assert agent.classify(state, "B1") == Verdict.CRIMINAL
    assert agent.classify(state, "A1") == Verdict.UNKNOWN


def test_inconsistent_knowledge_base_is_reported():
    state = make_state((
        fact("A1", Status.CRIMINAL, "criminal"),
        fact("A1", Status.INNOCENT, "innocent"),
    ))

    assert DeductiveAgent().classify(state, "B1") == Verdict.INCONSISTENT


def test_auto_solve_records_queries_and_revealed_clues(tmp_path):
    import json

    puzzle = {
        "name": "agent-chain",
        "size": 2,
        "initial_revealed": ["A1"],
        "characters": [
            {"cell": "A1", "name": "Ada", "profession": "Judge",
             "status": "INNOCENT",
             "clue": {"type": "FACT", "targets": ["B1"], "status": "CRIMINAL"}},
            {"cell": "B1", "name": "Ben", "profession": "Guard",
             "status": "CRIMINAL",
             "clue": {"type": "FACT", "targets": ["A2"], "status": "INNOCENT"}},
            {"cell": "A2", "name": "Cal", "profession": "Cook",
             "status": "INNOCENT",
             "clue": {"type": "FACT", "targets": ["B2"], "status": "INNOCENT"}},
            {"cell": "B2", "name": "Dee", "profession": "Clerk",
             "status": "INNOCENT",
             "clue": {"type": "FACT", "targets": ["A1"], "status": "INNOCENT"}},
        ],
    }
    path = tmp_path / "chain.json"
    path.write_text(json.dumps(puzzle), encoding="utf-8")

    from griductive.core.engine import GameEngine

    trace = DeductiveAgent().auto_solve(GameEngine.from_file(str(path)))

    assert trace.terminal == "SOLVED"
    assert [step.cell for step in trace.steps] == ["B1", "A2", "B2"]
    assert all(step.queries for step in trace.steps)
    assert all(step.revealed_clue_id for step in trace.steps)
    assert trace.steps[-1].queries[-1].assumption == "KB after final reveal"
    assert trace.to_dict()["terminal"] == "SOLVED"


def test_uniqueness_counts_distinct_primary_assignments():
    characters = make_state().characters
    assert count_solutions([], characters, limit=2) == 2
    assert not check_uniqueness([], characters)

    unique_facts = [
        fact("A1", Status.INNOCENT, "a1"),
        fact("B1", Status.CRIMINAL, "b1"),
    ]
    assert count_solutions(unique_facts, characters) == 1
    assert check_uniqueness(unique_facts, characters)

    impossible = unique_facts + [fact("A1", Status.CRIMINAL, "contradiction")]
    assert count_solutions(impossible, characters) == 0

    cardinality_unique = unique_facts + [
        Clue(
            id="one-criminal",
            type=ClueType.EXACTLY,
            region=Region(RegionKind.CELLS, cells=("A1", "B1")),
            k=1,
        )
    ]
    assert count_solutions(cardinality_unique, characters) == 1
