"""Resolve board regions to cells in deterministic row-major order."""
from __future__ import annotations

import re

from ..core.models import Region, RegionKind


_CELL_PATTERN = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")


def parse_cell(cell: str, size: int) -> tuple[int, int]:
    """Return zero-based (row, column), validating the cell against the board."""
    match = _CELL_PATTERN.fullmatch(cell)
    if match is None:
        raise ValueError("invalid cell id: {!r}".format(cell))
    column = 0
    for letter in match.group(1):
        column = column * 26 + ord(letter) - ord("A") + 1
    column -= 1
    row = int(match.group(2)) - 1
    if row >= size or column >= size:
        raise ValueError("cell {!r} is outside a {}x{} board".format(cell, size, size))
    return row, column


def cell_id(row: int, column: int) -> str:
    """Return the standard cell id for a zero-based coordinate."""
    letters = ""
    value = column + 1
    while value:
        value, remainder = divmod(value - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return "{}{}".format(letters, row + 1)


def cells_of(region: Region, size: int) -> list[str]:
    """Return unique cells for a region in row-major order."""
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")

    if region.kind == RegionKind.ROW:
        try:
            row = int(region.ref or "") - 1
        except ValueError as error:
            raise ValueError("ROW region ref must be a row number") from error
        if row < 0 or row >= size or str(row + 1) != region.ref:
            raise ValueError("ROW region ref is outside the board")
        return [cell_id(row, column) for column in range(size)]

    if region.kind == RegionKind.COL:
        if not region.ref or not region.ref.isascii() or not region.ref.isalpha() or not region.ref.isupper():
            raise ValueError("COL region ref is outside the board")
        column = 0
        for letter in region.ref:
            column = column * 26 + ord(letter) - ord("A") + 1
        column -= 1
        if column >= size:
            raise ValueError("COL region ref is outside the board")
        return [cell_id(row, column) for row in range(size)]

    if region.kind == RegionKind.NEIGHBORS:
        if region.ref is None:
            raise ValueError("NEIGHBORS region requires a cell ref")
        return neighbors(region.ref, size)

    if region.kind == RegionKind.CELLS:
        cells = list(region.cells)
        if len(set(cells)) != len(cells):
            raise ValueError("CELLS region cannot contain duplicate cells")
        coordinates = [(parse_cell(cell, size), cell) for cell in cells]
        return [cell for _, cell in sorted(coordinates)]

    raise ValueError("unsupported region kind: {!r}".format(region.kind))


def neighbors(cell: str, size: int) -> list[str]:
    """Return the in-bounds eight-direction neighbors of a cell."""
    row, column = parse_cell(cell, size)
    return [
        cell_id(next_row, next_column)
        for next_row in range(max(0, row - 1), min(size, row + 2))
        for next_column in range(max(0, column - 1), min(size, column + 2))
        if (next_row, next_column) != (row, column)
    ]
