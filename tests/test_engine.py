from griductive.core.engine import GameEngine
from griductive.core.models import Status, SubmitResult, Verdict


def test_load_and_public_state_hides_unrevealed():
    eng = GameEngine.from_file("puzzles/3x3/example_3x3.json")
    st = eng.public_state()
    assert st.size == 3
    assert len(st.revealed_clues) == 1 and set(st.proved) == {"A1"}


def test_not_provable_and_contradicted():
    eng = GameEngine.from_file("puzzles/3x3/example_3x3.json")
    assert eng.submit_verdict("B1", Status.CRIMINAL, lambda s, c: Verdict.UNKNOWN) == SubmitResult.NOT_PROVABLE
    assert eng.submit_verdict("B1", Status.CRIMINAL, lambda s, c: Verdict.INNOCENT) == SubmitResult.CONTRADICTED
    assert not eng.is_revealed("B1")
