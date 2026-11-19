"""GUI (Phần 1). Gợi ý: tkinter. Cần: lưới NxN, tọa độ, tên/nghề, thẻ úp/mở,
chọn clue -> highlight ô liên quan, nút Load / Restart / Hint / Auto Solve,
chọn ô rồi bấm CRIMINAL / INNOCENT, hiển thị NOT_PROVABLE / CONTRADICTED.

GUI chỉ gọi:  engine.public_state(), engine.submit_verdict(...),
              agent.hint(state), agent.auto_solve(engine)
"""
import tkinter as tk
from tkinter import filedialog  # noqa: F401  (dùng cho nút Load)


def run_gui() -> None:
    root = tk.Tk()
    root.title("Griductive Solver")
    # TODO(Phần 1): dựng GUI.
    tk.Label(root, text="Griductive Solver - TODO").pack(padx=40, pady=40)
    root.mainloop()
