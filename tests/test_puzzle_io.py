"""Test Phần 1: tọa độ lưới + kiểm tra lỗi file puzzle."""
import copy
import json

import pytest

from griductive.core import grid
from griductive.core.models import Region, RegionKind, Status
from griductive.core.puzzle_io import PuzzleError, load_puzzle, parse_puzzle

EXAMPLE = "puzzles/3x3/example_3x3.json"


# ---------- grid ----------
def test_parse_and_make_cell():
    assert grid.parse_cell("B3") == (3, 2)
    assert grid.make_cell(3, 2) == "B3"
    with pytest.raises(ValueError):
        grid.parse_cell("3B")


def test_neighbors_corner_edge_center():
    assert grid.neighbors("A1", 3) == ["B1", "A2", "B2"]
    assert len(grid.neighbors("B1", 3)) == 5
    assert len(grid.neighbors("B2", 3)) == 8
    assert "B2" not in grid.neighbors("B2", 3)


def test_region_cells():
    assert grid.region_cells(Region(RegionKind.ROW, "2"), 3) == ["A2", "B2", "C2"]
    assert grid.region_cells(Region(RegionKind.COL, "B"), 3) == ["B1", "B2", "B3"]
    assert grid.region_cells(Region(RegionKind.CELLS, cells=("C3", "A1")), 3) == ["A1", "C3"]
    for bad in (Region(RegionKind.ROW, "4"), Region(RegionKind.COL, "D"),
                Region(RegionKind.CELLS, cells=("A1", "A1")), Region(RegionKind.CELLS)):
        with pytest.raises(ValueError):
            grid.region_cells(bad, 3)


# ---------- puzzle_io ----------
def _data():
    with open(EXAMPLE, encoding="utf-8") as f:
        return json.load(f)


def test_load_example_ok():
    p = load_puzzle(EXAMPLE)
    assert p.size == 3 and len(p.characters) == 9
    assert [c.name for c in p.characters] == sorted(c.name for c in p.characters)
    assert p.solution["B1"] == Status.CRIMINAL
    assert p.clues["A1"].id == "clue_A1"


def _expect_error(mutate, text):
    d = copy.deepcopy(_data())
    mutate(d)
    with pytest.raises(PuzzleError, match=text):
        parse_puzzle(d)


def test_missing_field():
    _expect_error(lambda d: d.pop("size"), "size")


def test_wrong_number_of_characters():
    _expect_error(lambda d: d["characters"].pop(), "cần đúng 9")


def test_duplicate_cell():
    def m(d):
        d["characters"][1]["cell"] = "A1"
    _expect_error(m, "trùng")


def test_cell_outside_grid():
    def m(d):
        d["characters"][0]["cell"] = "D1"
    _expect_error(m, "không nằm trong lưới")


def test_bad_status():
    def m(d):
        d["characters"][0]["status"] = "GUILTY"
    _expect_error(m, "CRIMINAL/INNOCENT")


def test_initial_revealed_not_exist():
    def m(d):
        d["initial_revealed"] = ["Z9"]
    _expect_error(m, "initial_revealed")


def test_initial_revealed_empty():
    def m(d):
        d["initial_revealed"] = []
    _expect_error(m, "initial_revealed")


def test_k_out_of_range():
    def m(d):
        d["characters"][0]["clue"]["k"] = 9     # A1 chỉ có 3 ô kề
    _expect_error(m, "k phải")


def test_bad_region_and_type():
    def m1(d):
        d["characters"][3]["clue"]["region"]["ref"] = "7"
    _expect_error(m1, "Hàng không tồn tại")

    def m2(d):
        d["characters"][0]["clue"]["type"] = "MAYBE"
    _expect_error(m2, "clue.type")


def test_same_needs_two_distinct_targets():
    def m(d):
        d["characters"][4]["clue"]["targets"] = ["A2", "A2"]
    _expect_error(m, "KHÁC NHAU")


def test_duplicate_names():
    def m(d):
        d["characters"][1]["name"] = "Abel"
    _expect_error(m, "Tên nhân vật bị trùng")


def test_invalid_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{ size: 3", encoding="utf-8")
    with pytest.raises(PuzzleError, match="JSON"):
        load_puzzle(f)
