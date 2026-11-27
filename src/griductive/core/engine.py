"""Game Engine (Phần 1). Giữ hidden solution + clue chưa lật.

Engine KHÔNG tự suy luận. Để phân biệt NOT_PROVABLE / CONTRADICTED nó nhận một
`classifier` (callable) từ bên ngoài: classifier(PublicState, cell) -> Verdict.
Ở bản tích hợp, classifier = DeductiveAgent.classify (Phần 4).

Luồng submit_verdict(cell, claimed, classifier):
    1. Ô đã lật rồi                         -> ALREADY_REVEALED
    2. Hỏi classifier CHỈ với PublicState   -> v
    3. v = INCONSISTENT                     -> INCONSISTENT  (KB tự mâu thuẫn)
       v = UNKNOWN                          -> NOT_PROVABLE  (chưa đủ thông tin)
       v ngược với claimed                  -> CONTRADICTED  (thông tin chứng minh điều ngược lại)
       v = claimed                          -> đối chiếu đáp án ẩn rồi lật thẻ -> ACCEPTED
Mọi trường hợp bị từ chối: trạng thái game KHÔNG đổi, thẻ KHÔNG lật.
"""
from __future__ import annotations
from typing import Callable

from .models import Clue, PublicState, Status, SubmitResult, Verdict
from .puzzle_io import Puzzle, load_puzzle

Classifier = Callable[[PublicState, str], Verdict]


class PuzzleIntegrityError(RuntimeError):
    """Classifier chứng minh được một verdict nhưng đáp án ẩn lại khác.
    Chỉ xảy ra khi puzzle không có nghiệm duy nhất hoặc classifier bị lỗi.
    Engine KHÔNG lật thẻ trong trường hợp này."""


class GameEngine:
    def __init__(self, puzzle: Puzzle):
        self._puzzle = puzzle
        self.restart()

    @classmethod
    def from_file(cls, path: str) -> "GameEngine":
        return cls(load_puzzle(path))

    def restart(self) -> None:
        self._revealed: list[str] = []          # thứ tự lật
        self._proved: dict[str, Status] = {}
        for cell in self._puzzle.initial_revealed:   # face-up ban đầu
            self._reveal(cell)

    # ---- public read API (an toàn cho agent / GUI) ----
    @property
    def size(self) -> int:
        return self._puzzle.size

    @property
    def name(self) -> str:
        """Tên puzzle (để GUI hiện tiêu đề). Không phải thông tin bí mật."""
        return self._puzzle.name

    def public_state(self) -> PublicState:
        p = self._puzzle
        return PublicState(
            size=p.size,
            characters=tuple(p.characters),
            revealed_clues=tuple(p.clues[c] for c in self._revealed),
            proved=dict(self._proved),
        )

    def is_revealed(self, cell: str) -> bool:
        return cell in self._proved

    def is_solved(self) -> bool:
        return len(self._proved) == len(self._puzzle.characters)

    # ---- actions ----
    def submit_verdict(self, cell: str, claimed: Status, classifier: Classifier) -> SubmitResult:
        """Người chơi/agent gọi CRIMINAL hay INNOCENT cho `cell`."""
        if cell not in self._puzzle.solution:
            raise ValueError(f"Ô không tồn tại: {cell!r}")
        claimed = Status(claimed)          # chấp nhận cả chuỗi "CRIMINAL"
        if cell in self._proved:
            return SubmitResult.ALREADY_REVEALED
        # Classifier chỉ được thấy PublicState (bản sao), không thấy self._puzzle.
        v = Verdict(classifier(self.public_state(), cell))
        if v == Verdict.INCONSISTENT:
            return SubmitResult.INCONSISTENT
        if v == Verdict.UNKNOWN:
            return SubmitResult.NOT_PROVABLE
        if v.value != claimed.value:
            return SubmitResult.CONTRADICTED
        # Classifier nói "chứng minh được". Đáp án ẩn phải khớp; nếu không thì
        # puzzle có nhiều nghiệm (hoặc classifier sai) -> báo lỗi, không lật thẻ.
        if self._puzzle.solution[cell] != claimed:
            raise PuzzleIntegrityError(
                f"Classifier chứng minh {cell} = {claimed.value} nhưng đáp án ẩn khác. "
                "Puzzle có thể không có nghiệm duy nhất, hoặc classifier bị lỗi.")
        self._reveal(cell)
        return SubmitResult.ACCEPTED

    def get_clue(self, cell: str) -> Clue:
        """Chỉ trả về clue của thẻ ĐÃ lật."""
        if cell not in self._proved:
            raise PermissionError("Thẻ chưa lật")
        return self._puzzle.clues[cell]

    def _reveal(self, cell: str) -> None:
        self._proved[cell] = self._puzzle.solution[cell]
        self._revealed.append(cell)
