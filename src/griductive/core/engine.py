"""Game Engine (Phần 1). Giữ hidden solution + clue chưa lật.

Engine KHÔNG tự suy luận. Để phân biệt NOT_PROVABLE / CONTRADICTED nó nhận một
`classifier` (callable) từ bên ngoài: classifier(PublicState, cell) -> Verdict.
Ở bản tích hợp, classifier = DeductiveAgent.classify (Phần 4).
"""
from __future__ import annotations
from typing import Callable

from .models import Clue, PublicState, Status, SubmitResult, Verdict
from .puzzle_io import Puzzle, load_puzzle

Classifier = Callable[[PublicState, str], Verdict]


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
        if cell in self._proved:
            return SubmitResult.ALREADY_REVEALED
        v = classifier(self.public_state(), cell)
        if v == Verdict.INCONSISTENT:
            return SubmitResult.INCONSISTENT
        if v == Verdict.UNKNOWN:
            return SubmitResult.NOT_PROVABLE
        if v.value != claimed.value:
            return SubmitResult.CONTRADICTED
        assert self._puzzle.solution[cell] == claimed, "Puzzle không có nghiệm duy nhất?"
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
