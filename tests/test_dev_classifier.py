"""Test classifier tạm (CHỈ DÙNG ĐỂ DEV) + chơi hết puzzle qua Engine.

tests/fixtures/dev_solvable_*.json: puzzle nhỏ có nghiệm duy nhất và giải được
không cần đoán, để test GUI/Engine trong lúc chờ Phần 4.
"""
import pytest

from griductive.core import grid
from griductive.core.engine import GameEngine
from griductive.core.models import (Character, Clue, ClueType, PublicState, Region,
                                    RegionKind, Status, SubmitResult, Verdict)
from griductive.gui.dev_classifier import dev_classify


def _play_all(path):
    """Mỗi bước: chọn ô bị ép buộc đầu tiên theo row-major, nộp verdict."""
    eng = GameEngine.from_file(path)
    steps = 0
    while not eng.is_solved():
        st = eng.public_state()
        forced = [(c, dev_classify(st, c)) for c in grid.all_cells(st.size) if c not in st.proved]
        forced = [(c, v) for c, v in forced if v in (Verdict.CRIMINAL, Verdict.INNOCENT)]
        assert forced, f"Bị kẹt sau {steps} bước"
        cell, v = forced[0]
        assert eng.submit_verdict(cell, Status(v.value), dev_classify) == SubmitResult.ACCEPTED
        steps += 1
    return steps


@pytest.mark.parametrize("path", ["tests/fixtures/dev_solvable_3x3.json",
                                  "tests/fixtures/dev_solvable_4x4.json"])
def test_fixture_solvable_without_guessing(path):
    assert _play_all(path) > 0


def test_example_3x3_is_stuck_at_start():
    """example_3x3.json (của nhóm) bị kẹt ngay: không ô nào bị ép buộc."""
    st = GameEngine.from_file("puzzles/3x3/example_3x3.json").public_state()
    assert all(dev_classify(st, c) == Verdict.UNKNOWN for c in grid.all_cells(3) if c not in st.proved)


def _state(clues, proved=None):
    chars = tuple(Character(c, c, "x") for c in grid.all_cells(2))
    return PublicState(2, chars, tuple(clues), proved or {})


def test_fact_clue_forces_cell():
    st = _state([Clue("c1", ClueType.FACT, ("A1",), Status.CRIMINAL)])
    assert dev_classify(st, "A1") == Verdict.CRIMINAL
    assert dev_classify(st, "B2") == Verdict.UNKNOWN     # không clue nào nhắc tới


def test_inconsistent_kb():
    st = _state([Clue("c1", ClueType.FACT, ("A1",), Status.CRIMINAL),
                 Clue("c2", ClueType.FACT, ("A1",), Status.INNOCENT)])
    assert dev_classify(st, "B1") == Verdict.INCONSISTENT


def test_counting_with_proved():
    # Đúng 1 tội phạm trong hàng 1; A1 đã biết là vô tội -> B1 là tội phạm.
    st = _state([Clue("c1", ClueType.EXACTLY, region=Region(RegionKind.ROW, "1"), k=1)],
                {"A1": Status.INNOCENT})
    assert dev_classify(st, "B1") == Verdict.CRIMINAL
    assert dev_classify(st, "A2") == Verdict.UNKNOWN
