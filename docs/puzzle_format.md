# Định dạng puzzle JSON
- `size`: N. `initial_revealed`: danh sách cell face-up ban đầu.
- `characters[]`: `cell`, `name`, `profession`, `status` (HIDDEN, chỉ Engine đọc), `clue`.
- `clue.type`: FACT | SAME | DIFFERENT | EXACTLY | AT_LEAST | AT_MOST | (mở rộng: PARITY, COMPARE)
- `clue.targets`: FACT -> [cell] (+ `status`); SAME/DIFFERENT -> [cell_i, cell_j]
- `clue.region`: `{"kind": "ROW"|"COL"|"NEIGHBORS"|"CELLS", "ref": "...", "cells": [...]}` ; `clue.k`: số nguyên.
- `example_3x3.json` chỉ để test định dạng, CHƯA kiểm tra nghiệm duy nhất
  (dùng `agent/uniqueness.py` để verify khi làm xong).
