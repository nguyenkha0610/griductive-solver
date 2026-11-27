"""Test bộ điều khiển GUI (không cần tkinter, không cần Phần 4)."""
from griductive.agent.trace import DeductionTrace, TraceStep
from griductive.core.models import Status, Verdict
from griductive.gui.controller import GameController

FIX3 = "tests/fixtures/dev_solvable_3x3.json"
EXAMPLE = "puzzles/3x3/example_3x3.json"


class StubAgent:
    """Agent giả để test nhánh 'Phần 4 đã xong'. Không đọc đáp án ẩn."""
    def __init__(self, hint=None):
        self._hint = hint
        self.classify_calls = 0

    def classify(self, state, cell):
        self.classify_calls += 1
        return Verdict.UNKNOWN

    def hint(self, state):
        return self._hint

    def auto_solve(self, engine):
        return DeductionTrace([TraceStep(1, ["clue_C1"], cell="B1", verdict=Verdict.INNOCENT,
                                         revealed_clue_id="clue_B1")], "SOLVED")


def test_nothing_loaded_is_safe():
    c = GameController()
    for m in (c.submit(Status.CRIMINAL), c.hint(), c.auto_solve(), c.restart()):
        assert m.kind == "warn"
    assert "Load" in c.title()


def test_load_bad_file_reports_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"size": 3}', encoding="utf-8")
    c = GameController()
    assert c.load(str(bad)).kind == "error"
    assert c.load(str(tmp_path / "missing.json")).kind == "error"
    assert not c.loaded


def test_cells_view_only_public_info():
    c = GameController()
    c.load(FIX3)
    views = c.cells()
    assert [v.cell for v in views][:3] == ["A1", "B1", "C1"]
    up = [v for v in views if v.face_up]
    assert [v.cell for v in up] == ["C1"] and up[0].clue_text
    down = [v for v in views if not v.face_up]
    assert all(v.status is None and v.clue_text is None for v in down)


def test_submit_flow_with_dev_classifier_fallback():
    """Phần 4 chưa xong -> controller dùng classifier tạm và báo rõ."""
    c = GameController()
    c.load(FIX3)
    c.select_cell("A1")
    m = c.submit(Status.CRIMINAL)
    assert m.kind == "warn" and "NOT_PROVABLE" in m.text
    assert c.using_dev_classifier and "TẠM" in c.classifier_label()
    # Clue C1: "Không có tội phạm nào trong các ô kề Ivy (C3)" -> B2 vô tội.
    c.select_cell("B2")
    assert "CONTRADICTED" in c.submit(Status.CRIMINAL).text
    m = c.submit(Status.INNOCENT)
    assert m.kind == "ok" and "ĐÚNG" in m.text
    assert c.selected_clue_id == "clue_B2"      # clue mới lật được tô sáng
    assert any(v.cell == "B2" and v.status == Status.INNOCENT for v in c.cells())
    assert "đã được lật" in c.submit(Status.INNOCENT).text


def test_restart_resets_board():
    c = GameController()
    c.load(FIX3)
    c.select_cell("B2")
    c.submit(Status.INNOCENT)
    c.restart()
    assert [v.cell for v in c.cells() if v.face_up] == ["C1"]
    assert c.selected_cell is None


def test_select_clue_highlight_toggle():
    c = GameController()
    c.load(EXAMPLE)
    c.select_clue("clue_A1")
    h = c.highlight()
    assert h.counted == {"B1", "A2", "B2"} and h.anchors == {"A1"}
    c.select_clue("clue_A1")                     # bấm lần nữa -> bỏ chọn
    assert not c.highlight().all


def test_hint_and_autosolve_wait_for_part4():
    c = GameController()
    c.load(FIX3)
    assert "chờ Phần 4" in c.hint().text
    assert "chờ Phần 4" in c.auto_solve().text


def test_with_finished_agent_no_fallback():
    agent = StubAgent(hint=("B2", Verdict.INNOCENT))
    c = GameController(agent=agent)
    c.load(FIX3)
    c.select_cell("B2")
    assert "NOT_PROVABLE" in c.submit(Status.INNOCENT).text
    assert agent.classify_calls == 1 and not c.using_dev_classifier
    m = c.hint()
    assert "B2" in m.text and c.hint_cell == "B2" and c.selected_clue_id == "clue_C1"
    m = c.auto_solve()
    assert m.kind == "ok" and m.details == ["Bước 1: B1 -> INNOCENT | 0 truy vấn SAT | lật clue_B1"]


def test_agent_crash_does_not_crash_gui():
    class Broken(StubAgent):
        def classify(self, state, cell):
            raise ZeroDivisionError("bug")
    c = GameController(agent=Broken())
    c.load(FIX3)
    c.select_cell("A1")
    assert c.submit(Status.CRIMINAL).kind == "error"


def test_play_whole_puzzle_through_controller():
    from griductive.core import grid
    from griductive.gui.dev_classifier import dev_classify
    c = GameController()
    c.load(FIX3)
    while not c.engine.is_solved():
        st = c.state()
        cell, v = next((x, dev_classify(st, x)) for x in grid.all_cells(3)
                       if x not in st.proved and dev_classify(st, x) in (Verdict.CRIMINAL, Verdict.INNOCENT))
        c.select_cell(cell)
        assert c.submit(Status(v.value)).kind == "ok"
    assert "ĐÃ GIẢI XONG" in c.title()
