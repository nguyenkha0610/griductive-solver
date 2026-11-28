# Phụ lục — Cách dùng Generative AI (Phần 1)

Công cụ: Claude (Anthropic), dùng như trợ lý lập trình.

## Cách dùng
- Đọc đề + repo nhóm và tóm tắt luật chơi, phạm vi Phần 1, phần phụ thuộc vào nhóm khác.
- Đề xuất chia nhỏ công việc; viết code theo từng bước nhỏ, mỗi bước kèm test pytest.
- Rà soát `engine.py` có sẵn, chỉ ra lỗ hổng (assert, thiếu kiểm tra file puzzle).
- Sinh hai puzzle nhỏ giải được để test GUI (`tests/fixtures/`), kiểm tra bằng thử mọi khả năng.
- Viết nháp báo cáo Phần 1 và sơ đồ kiến trúc.

## Kiểm soát
- Mọi code đều chạy `pytest` trước khi commit. Người thực hiện đọc lại và chạy GUI trên Windows.
- Không để AI sửa `core/models.py` hay chữ ký hàm "hợp đồng" của nhóm.
- Classifier tạm chỉ dùng `PublicState`, không đọc đáp án ẩn; sẽ thay bằng agent của Phần 4.

## Prompt đã dùng (tóm tắt theo thứ tự)
1. Prompt khởi đầu (đầy đủ trong `prompt_phan1_griductive.md`): giới thiệu bản thân và môn học,
   tài liệu (đề PDF, repo, file chia việc), việc của Phần 1, quy tắc nhóm (nhánh
   `feat/p1-engine-gui`, commit `[P1] ...`, không sửa models.py, GUI không đọc `engine._puzzle`,
   bắt NotImplementedError, test pytest, chạy trên Windows), cách làm việc (tóm tắt → task list →
   từng bước nhỏ → kiểm tra engine → ảnh chụp → báo cáo → ôn vấn đáp). Yêu cầu trả lời tiếng Việt,
   giải thích thuật ngữ bằng ví dụ đời thường.
2. "Trở ngại 1 và 3 t giải quyết rồi đó, check thử." (kiểm tra quyền GitHub và file chia việc)
3. Gửi lại link repo GitHub.
4. "Giờ làm được gì cứ làm đi, đến chỗ nào cần đợi người khác làm thì bảo t."
5. Hỏi cách chạy lệnh trên Windows từ đầu, cách lưu ảnh chụp màn hình (Paint / Snipping Tool).
6. "Check GitHub xem còn gì không." (sau khi Phần 2–5 đã gộp: chạy lại toàn bộ test, chạy Hint /
   Auto Solve qua GUI với mọi puzzle, liệt kê việc còn thiếu của Phần 1)
7. "Phần nào của t làm được thì làm đi." (cập nhật báo cáo theo agent đã tích hợp, thêm thông báo
   "Đang tự giải..." cho nút Auto Solve)
