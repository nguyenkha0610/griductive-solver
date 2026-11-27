import pytest

from griductive.core.engine import GameEngine, PuzzleIntegrityError
from griductive.core.models import Status, SubmitResult, Verdict

EXAMPLE = "puzzles/3x3/example_3x3.json"


def test_load_and_public_state_hides_unrevealed():
    eng = GameEngine.from_file(EXAMPLE)
    st = eng.public_state()
    assert st.size == 3
    assert len(st.revealed_clues) == 1 and set(st.proved) == {"A1"}


def test_not_provable_and_contradicted():
    eng = GameEngine.from_file(EXAMPLE)
    assert eng.submit_verdict("B1", Status.CRIMINAL, lambda s, c: Verdict.UNKNOWN) == SubmitResult.NOT_PROVABLE
    assert eng.submit_verdict("B1", Status.CRIMINAL, lambda s, c: Verdict.INNOCENT) == SubmitResult.CONTRADICTED
    assert not eng.is_revealed("B1")


def test_public_state_has_no_secret_fields():
    st = GameEngine.from_file(EXAMPLE).public_state()
    assert not hasattr(st, "solution")
    assert {c.id for c in st.revealed_clues} == {"clue_A1"}   # chỉ clue đã lật
    assert all(not hasattr(ch, "status") for ch in st.characters)


def test_accept_reveals_card_and_clue():
    eng = GameEngine.from_file(EXAMPLE)
    r = eng.submit_verdict("B1", Status.CRIMINAL, lambda s, c: Verdict.CRIMINAL)
    assert r == SubmitResult.ACCEPTED
    st = eng.public_state()
    assert st.proved["B1"] == Status.CRIMINAL
    assert [c.id for c in st.revealed_clues] == ["clue_A1", "clue_B1"]   # đúng thứ tự lật
    assert eng.get_clue("B1").id == "clue_B1"


def test_rejected_verdict_does_not_change_state():
    eng = GameEngine.from_file(EXAMPLE)
    before = eng.public_state()
    eng.submit_verdict("B1", Status.INNOCENT, lambda s, c: Verdict.UNKNOWN)
    eng.submit_verdict("B1", Status.INNOCENT, lambda s, c: Verdict.CRIMINAL)
    assert eng.public_state() == before


def test_already_revealed_and_inconsistent():
    eng = GameEngine.from_file(EXAMPLE)
    assert eng.submit_verdict("A1", Status.INNOCENT, lambda s, c: Verdict.INNOCENT) == SubmitResult.ALREADY_REVEALED
    assert eng.submit_verdict("B2", Status.INNOCENT, lambda s, c: Verdict.INCONSISTENT) == SubmitResult.INCONSISTENT


def test_classifier_only_receives_public_state():
    eng = GameEngine.from_file(EXAMPLE)
    seen = []
    eng.submit_verdict("B1", Status.CRIMINAL, lambda s, c: seen.append((s, c)) or Verdict.UNKNOWN)
    (state, cell), = seen
    assert cell == "B1" and type(state).__name__ == "PublicState"


def test_wrong_classifier_does_not_reveal():
    """Classifier nói INNOCENT nhưng đáp án ẩn là CRIMINAL -> lỗi rõ ràng, không lật."""
    eng = GameEngine.from_file(EXAMPLE)
    with pytest.raises(PuzzleIntegrityError):
        eng.submit_verdict("B1", Status.INNOCENT, lambda s, c: Verdict.INNOCENT)
    assert not eng.is_revealed("B1")


def test_restart_and_unknown_cell():
    eng = GameEngine.from_file(EXAMPLE)
    eng.submit_verdict("B1", Status.CRIMINAL, lambda s, c: Verdict.CRIMINAL)
    eng.restart()
    assert set(eng.public_state().proved) == {"A1"}
    with pytest.raises(ValueError):
        eng.submit_verdict("Z9", Status.CRIMINAL, lambda s, c: Verdict.CRIMINAL)


def test_get_clue_of_face_down_card_is_forbidden():
    eng = GameEngine.from_file(EXAMPLE)
    with pytest.raises(PermissionError):
        eng.get_clue("B1")
