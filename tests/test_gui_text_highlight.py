"""Test Phần 1: câu chữ của clue + ô cần tô sáng (không cần tkinter)."""
from griductive.core.models import Character, Clue, ClueType, Region, RegionKind, Status
from griductive.core.puzzle_io import load_puzzle
from griductive.gui.clue_text import clue_to_text
from griductive.gui.highlight import clue_highlight, clue_owner

P = load_puzzle("puzzles/3x3/example_3x3.json")
CH = P.characters


def test_text_counting_clues():
    assert clue_to_text(P.clues["A1"], CH) == "Có đúng 1 tội phạm trong các ô kề Abel (A1)."
    assert clue_to_text(P.clues["A2"], CH) == "Có nhiều nhất 1 tội phạm trong hàng 2."
    assert clue_to_text(P.clues["C2"], CH) == "Có ít nhất 1 tội phạm trong cột B."
    assert clue_to_text(P.clues["A3"], CH) == "Không có tội phạm nào trong các ô A2, A3."


def test_text_binary_and_fact():
    assert clue_to_text(P.clues["B1"], CH).startswith("Abel (A1) và Bea (B1) KHÁC")
    assert clue_to_text(P.clues["B2"], CH).startswith("Derek (A2) và Eliza (B2) CÙNG")
    assert clue_to_text(P.clues["C1"], CH) == "Clara (C1) là VÔ TỘI."


def test_text_extension_never_crashes():
    c = Clue("clue_X", ClueType.COMPARE, extra={"op": ">"})
    assert "COMPARE" in clue_to_text(c, CH)
    par = Clue("clue_Y", ClueType.PARITY, region=Region(RegionKind.ROW, "1"), extra={"parity": "even"})
    assert clue_to_text(par, CH) == "Số tội phạm trong hàng 1 là số CHẴN."


def test_highlight_regions():
    h = clue_highlight(P.clues["A1"], 3)            # NEIGHBORS A1
    assert h.counted == {"B1", "A2", "B2"} and h.anchors == {"A1"}
    assert clue_highlight(P.clues["C3"], 3).counted == {"B1", "B2", "B3"}   # cột B
    assert clue_highlight(P.clues["B2"], 3).counted == {"A2", "B2"}         # SAME
    assert clue_highlight(P.clues["C1"], 3).counted == {"C1"}               # FACT


def test_highlight_extension_regions_in_extra():
    c = Clue("clue_Z", ClueType.COMPARE,
             extra={"region_a": {"kind": "ROW", "ref": "1"}, "region_b": {"kind": "COL", "ref": "C"}})
    assert clue_highlight(c, 3).counted == {"A1", "B1", "C1", "C2", "C3"}


def test_clue_owner():
    assert clue_owner(P.clues["B3"]) == "B3"
