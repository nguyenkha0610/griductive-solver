# Quy trình làm việc nhóm

## Branch
- `main`: luôn chạy được, chỉ merge qua Pull Request (≥1 người review).
- Mỗi người 1 nhánh: `feat/p1-engine-gui`, `feat/p2-cnf`, `feat/p3-dpll`, `feat/p4-agent`, `feat/p5-experiments`.
- Commit: `[P2] add exactly-k encoding`.

## Quy tắc
1. Không sửa `core/models.py` hoặc chữ ký hàm "hợp đồng" nếu chưa báo nhóm.
2. Logic Agent / Encoder chỉ nhận `PublicState`, **không import** `puzzle_io.Puzzle` hay `engine._puzzle`.
3. Không hard-code CNF cho từng puzzle.
4. Mỗi PR kèm test trong `tests/`; bỏ `skip` khi module xong.
5. Giữ lại log các case fail/timeout, không xóa khỏi kết quả.

## Timeline gợi ý (3 tuần)
- Tuần 1: P1–P4 cài theo interface (stub → bản chạy được); P5 dựng puzzle test + script.
- Tuần 2: tích hợp, chạy thử, sửa lỗi; P3 và P4 quay video phần của mình.
- Tuần 3: thực nghiệm, báo cáo, dựng video, kiểm tra link Drive (cửa sổ ẩn danh), nộp zip `StudentID1_StudentID2_...`.

## Cấu trúc nộp bài
`StudentID1_.../Source/{main.py, README.md, requirements.txt, ...}` + `Report.pdf` (kèm link video).
