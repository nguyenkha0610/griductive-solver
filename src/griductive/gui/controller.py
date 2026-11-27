"""Bộ điều khiển GUI (Phần 1) — xử lý nút bấm, KHÔNG phụ thuộc tkinter.

Tách riêng khỏi app.py để test được bằng pytest (không cần mở cửa sổ).
app.py chỉ: vẽ dữ liệu lấy từ controller + gọi hàm của controller khi bấm nút.

Controller chỉ dùng API công khai:
    GameEngine.from_file / restart / public_state / submit_verdict / is_solved / name
    agent.classify (làm classifier cho submit_verdict), agent.hint, agent.auto_solve
KHÔNG đọc engine._puzzle (đáp án ẩn, clue chưa lật).

Agent Phần 4 được dùng mặc định. dev_classifier chỉ là fallback cho agent
được inject mà vẫn raise NotImplementedError trong quá trình phát triển.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..core import grid
from ..core.engine import GameEngine, PuzzleIntegrityError
from ..core.models import PublicState, Status, SubmitResult, Verdict
from ..core.puzzle_io import PuzzleError
from .clue_text import STATUS_VI, clue_to_text
from .dev_classifier import dev_classify
from .highlight import Highlight, clue_highlight, clue_owner

NO_HIGHLIGHT = Highlight(frozenset(), frozenset())


@dataclass
class Message:
    kind: str          # "ok" | "info" | "warn" | "error"
    text: str
    details: list[str] = field(default_factory=list)   # vd: các dòng trace của Auto Solve


@dataclass(frozen=True)
class CellView:
    """Những gì GUI cần để vẽ 1 thẻ. Chỉ chứa thông tin CÔNG KHAI."""
    cell: str
    row: int
    col: int
    name: str
    profession: str
    status: Optional[Status]      # None = chưa biết (thẻ úp)
    clue_id: Optional[str]        # chỉ có khi thẻ đã lật
    clue_text: Optional[str]

    @property
    def face_up(self) -> bool:
        return self.status is not None


@dataclass(frozen=True)
class ClueView:
    clue_id: str
    owner: str        # ô của người giữ thẻ
    text: str


def _default_agent():
    from ..agent.deductive_agent import DeductiveAgent
    return DeductiveAgent()


class GameController:
    def __init__(self, agent=None, dev_fallback: bool = True):
        self.agent = agent if agent is not None else _default_agent()
        self.dev_fallback = dev_fallback
        self.engine: Optional[GameEngine] = None
        self.using_dev_classifier = False
        self.selected_cell: Optional[str] = None
        self.selected_clue_id: Optional[str] = None
        self.hint_cell: Optional[str] = None

    # ------------------------------------------------------------ đọc trạng thái
    @property
    def loaded(self) -> bool:
        return self.engine is not None

    def state(self) -> PublicState:
        return self.engine.public_state()

    def title(self) -> str:
        if not self.loaded:
            return "Chưa mở puzzle — bấm Load"
        st = self.state()
        done = " — ĐÃ GIẢI XONG!" if self.engine.is_solved() else ""
        return f"{self.engine.name} ({st.size}x{st.size}) — đã biết {len(st.proved)}/{st.size ** 2}{done}"

    def classifier_label(self) -> str:
        if self.using_dev_classifier:
            return "Classifier: TẠM (dev, brute force) — chờ DeductiveAgent của Phần 4"
        return "Classifier: DeductiveAgent (Phần 4)"

    def cells(self) -> list[CellView]:
        st = self.state()
        by_cell = {c.cell: c for c in st.characters}
        clue_of = {clue_owner(cl): cl for cl in st.revealed_clues}
        out = []
        for cell in grid.all_cells(st.size):
            ch = by_cell[cell]
            r, c = grid.parse_cell(cell)
            clue = clue_of.get(cell)
            out.append(CellView(cell, r, c, ch.name, ch.profession, st.proved.get(cell),
                                clue.id if clue else None,
                                clue_to_text(clue, st.characters) if clue else None))
        return out

    def revealed_clues(self) -> list[ClueView]:
        st = self.state()
        return [ClueView(cl.id, clue_owner(cl), clue_to_text(cl, st.characters))
                for cl in st.revealed_clues]

    def highlight(self) -> Highlight:
        """Các ô cần tô sáng theo clue đang chọn."""
        if not self.loaded or self.selected_clue_id is None:
            return NO_HIGHLIGHT
        st = self.state()
        for cl in st.revealed_clues:
            if cl.id == self.selected_clue_id:
                return clue_highlight(cl, st.size)
        return NO_HIGHLIGHT

    def name_of(self, cell: str) -> str:
        for ch in self.state().characters:
            if ch.cell == cell:
                return f"{ch.name} ({cell})"
        return cell

    # ------------------------------------------------------------ chọn
    def select_cell(self, cell: Optional[str]) -> None:
        self.selected_cell = cell

    def select_clue(self, clue_id: Optional[str]) -> None:
        # bấm lại clue đang chọn = bỏ chọn
        self.selected_clue_id = None if clue_id == self.selected_clue_id else clue_id

    def _reset_selection(self) -> None:
        self.selected_cell = self.selected_clue_id = self.hint_cell = None

    # ------------------------------------------------------------ nút Load / Restart
    def load(self, path: str) -> Message:
        try:
            engine = GameEngine.from_file(path)
        except PuzzleError as e:
            return Message("error", f"File puzzle không hợp lệ: {e}")
        except OSError as e:
            return Message("error", f"Không mở được file: {e}")
        self.engine = engine
        self._reset_selection()
        return Message("info", f"Đã mở puzzle '{engine.name}'. Chọn một ô rồi bấm CRIMINAL hoặc INNOCENT.")

    def restart(self) -> Message:
        if not self.loaded:
            return Message("warn", "Chưa mở puzzle nào.")
        self.engine.restart()
        self._reset_selection()
        return Message("info", "Đã chơi lại từ đầu.")

    # ------------------------------------------------------------ verdict
    def _classify(self, state: PublicState, cell: str) -> Verdict:
        """Classifier đưa cho Engine. Ưu tiên agent thật của Phần 4."""
        try:
            v = self.agent.classify(state, cell)
            self.using_dev_classifier = False
            return v
        except NotImplementedError:
            if not self.dev_fallback:
                raise
            self.using_dev_classifier = True
            return dev_classify(state, cell)

    def submit(self, claimed: Status) -> Message:
        if not self.loaded:
            return Message("warn", "Chưa mở puzzle nào. Bấm Load trước.")
        cell = self.selected_cell
        if cell is None:
            return Message("warn", "Hãy bấm chọn một ô trên lưới trước.")
        who = self.name_of(cell)
        claimed = Status(claimed)
        try:
            res = self.engine.submit_verdict(cell, claimed, self._classify)
        except NotImplementedError:
            return Message("warn", "Chưa phân loại được: chờ DeductiveAgent.classify (Phần 4).")
        except PuzzleIntegrityError as e:
            return Message("error", f"Lỗi puzzle/classifier: {e}")
        except Exception as e:     # agent lỗi -> báo, không làm sập GUI
            return Message("error", f"Classifier gặp lỗi ({type(e).__name__}): {e}")

        if res == SubmitResult.ACCEPTED:
            self.hint_cell = None
            self.selected_clue_id = f"clue_{cell}"      # tô sáng clue vừa lật
            clue = next(c for c in self.revealed_clues() if c.owner == cell)
            msg = f"ĐÚNG! {who} là {STATUS_VI[claimed]}. Thẻ đã lật: “{clue.text}”"
            if self.engine.is_solved():
                msg += "  🎉 Đã giải xong puzzle!"
            return Message("ok", msg)
        if res == SubmitResult.NOT_PROVABLE:
            return Message("warn", f"TỪ CHỐI — NOT_PROVABLE: thông tin hiện có chưa đủ để chứng minh "
                                   f"{who} là {STATUS_VI[claimed]} (cũng chưa chứng minh được điều ngược lại). "
                                   "Thẻ không lật.")
        if res == SubmitResult.CONTRADICTED:
            return Message("error", f"TỪ CHỐI — CONTRADICTED: thông tin hiện có chứng minh {who} "
                                    f"KHÔNG phải {STATUS_VI[claimed]}. Thẻ không lật.")
        if res == SubmitResult.ALREADY_REVEALED:
            return Message("info", f"{who} đã được lật rồi.")
        return Message("error", "INCONSISTENT: các clue đã lật mâu thuẫn nhau (puzzle lỗi).")

    # ------------------------------------------------------------ Hint / Auto Solve
    def hint(self) -> Message:
        if not self.loaded:
            return Message("warn", "Chưa mở puzzle nào.")
        if self.engine.is_solved():
            return Message("info", "Puzzle đã giải xong, không cần gợi ý.")
        try:
            h = self.agent.hint(self.state())
        except NotImplementedError:
            return Message("warn", "Chức năng Hint đang chờ Phần 4 (DeductiveAgent.hint chưa cài).")
        except Exception as e:
            return Message("error", f"Hint gặp lỗi ({type(e).__name__}): {e}")
        if not h:
            return Message("warn", "Không có ô nào chứng minh được ở bước này (bị kẹt).")
        cell, verdict = h[0], Verdict(h[1])
        self.hint_cell = self.selected_cell = cell
        # Clue đã lật nào nhắc tới ô này -> chọn để tô sáng
        st = self.state()
        related = [cl for cl in st.revealed_clues if cell in clue_highlight(cl, st.size).all]
        self.selected_clue_id = related[0].id if related else None
        text = f"GỢI Ý: có thể chứng minh {self.name_of(cell)} là {verdict.value}."
        if related:
            text += " Xem clue: " + "; ".join(f"[{clue_owner(c)}] {clue_to_text(c, st.characters)}"
                                              for c in related)
        return Message("info", text)

    def auto_solve(self) -> Message:
        if not self.loaded:
            return Message("warn", "Chưa mở puzzle nào.")
        try:
            trace = self.agent.auto_solve(self.engine)
        except NotImplementedError:
            return Message("warn", "Chức năng Auto Solve đang chờ Phần 4 (DeductiveAgent.auto_solve chưa cài).")
        except Exception as e:
            return Message("error", f"Auto Solve gặp lỗi ({type(e).__name__}): {e}")
        self._reset_selection()
        lines = [self._trace_line(s) for s in getattr(trace, "steps", [])]
        terminal = getattr(trace, "terminal", "") or "?"
        kind = "ok" if terminal == "SOLVED" else "warn"
        return Message(kind, f"Auto Solve kết thúc: {terminal} sau {len(lines)} bước.", lines)

    @staticmethod
    def _trace_line(step) -> str:
        verdict = getattr(step, "verdict", None)
        v = getattr(verdict, "value", verdict)
        n_q = len(getattr(step, "queries", []) or [])
        clue = getattr(step, "revealed_clue_id", None)
        return (f"Bước {getattr(step, 'step', '?')}: {getattr(step, 'cell', '?')} -> {v}"
                f" | {n_q} truy vấn SAT | lật {clue or '-'}")
