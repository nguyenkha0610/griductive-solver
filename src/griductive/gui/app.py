"""GUI tkinter (Phần 1).

Màn hình:
  [Load] [Restart] [Hint] [Auto Solve]   tên puzzle / tiến độ
  +--------------------+  +----------------------------------+
  |   A    B    C      |  | Ô đang chọn: ...                 |
  | 1 [ ] [ ] [ ]      |  | [CRIMINAL]  [INNOCENT]           |
  | 2 [ ] [ ] [ ]      |  | Clue đã lật (bấm để tô sáng)     |
  | 3 [ ] [ ] [ ]      |  | Thông báo (NOT_PROVABLE, ...)    |
  +--------------------+  +----------------------------------+
  thanh trạng thái: classifier đang dùng + chú thích màu

File này CHỈ vẽ. Mọi xử lý nằm trong controller.py (test được không cần cửa sổ).
GUI chỉ gọi engine.public_state()/submit_verdict(...) và agent.hint/auto_solve
thông qua controller; KHÔNG đọc engine._puzzle.
Phím tắt: C = CRIMINAL, I = INNOCENT, H = Hint, R = Restart, Ctrl+O = Load.
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from ..core.models import Status
from .controller import CellView, GameController, Message

# ---- màu sắc ----
COLOR = {
    "criminal": "#f4c2c2", "criminal_text": "#b03030",
    "innocent": "#c6ebc6", "innocent_text": "#2e7d32",
    "facedown": "#e6e6e6", "facedown_text": "#8a8a8a",
    "border": "#9e9e9e",
    "selected": "#1f6fd1",      # ô đang chọn
    "counted": "#f39c12",       # ô được clue đếm / nhắc tới
    "hint": "#8e44ad",          # ô được Hint gợi ý
    "bg": "#faf7f0",
}
MSG_COLOR = {"ok": "#2e7d32", "info": "#333333", "warn": "#c77700", "error": "#c62828"}
FONT = "Segoe UI"
HEADER = 26          # chỗ cho tọa độ A, B, C / 1, 2, 3
PAD = 6              # khoảng cách giữa các thẻ


def _puzzles_dir() -> str:
    d = Path(__file__).resolve().parents[3] / "puzzles"
    return str(d) if d.is_dir() else str(Path.cwd())


class GriductiveApp:
    def __init__(self, root: tk.Tk, controller: GameController | None = None):
        self.root = root
        self.ctl = controller or GameController()
        root.title("Griductive Solver")
        root.configure(bg=COLOR["bg"])
        self._clue_ids: list[str] = []     # clue id theo thứ tự trong Listbox
        self._build()
        self.refresh()

    # ================================================================ dựng giao diện
    def _build(self) -> None:
        r = self.root
        top = tk.Frame(r, bg=COLOR["bg"])
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)
        for text, cmd in (("📂 Load", self.on_load), ("↺ Restart", self.on_restart),
                          ("💡 Hint", self.on_hint), ("⚡ Auto Solve", self.on_auto_solve)):
            tk.Button(top, text=text, command=cmd, font=(FONT, 10), padx=8).pack(side=tk.LEFT, padx=3)
        self.title_var = tk.StringVar()
        tk.Label(top, textvariable=self.title_var, font=(FONT, 11, "bold"),
                 bg=COLOR["bg"]).pack(side=tk.LEFT, padx=14)

        main = tk.Frame(r, bg=COLOR["bg"])
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8)

        # ---- lưới ----
        self.canvas = tk.Canvas(main, bg=COLOR["bg"], highlightthickness=0, width=560, height=560)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", lambda e: self.draw_grid())

        # ---- cột bên phải ----
        side = tk.Frame(main, bg=COLOR["bg"], width=380)
        side.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.sel_var = tk.StringVar()
        tk.Label(side, textvariable=self.sel_var, font=(FONT, 11), bg=COLOR["bg"],
                 wraplength=360, justify=tk.LEFT).pack(anchor="w", pady=(0, 4))
        btns = tk.Frame(side, bg=COLOR["bg"])
        btns.pack(anchor="w", pady=4)
        tk.Button(btns, text="CRIMINAL (C)", bg=COLOR["criminal"], fg=COLOR["criminal_text"],
                  font=(FONT, 11, "bold"), width=13,
                  command=lambda: self.on_verdict(Status.CRIMINAL)).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(btns, text="INNOCENT (I)", bg=COLOR["innocent"], fg=COLOR["innocent_text"],
                  font=(FONT, 11, "bold"), width=13,
                  command=lambda: self.on_verdict(Status.INNOCENT)).pack(side=tk.LEFT)

        tk.Label(side, text="Clue đã lật (bấm để tô sáng các ô liên quan):", font=(FONT, 10, "bold"),
                 bg=COLOR["bg"]).pack(anchor="w", pady=(10, 2))
        self.clue_list = tk.Listbox(side, width=52, height=10, font=(FONT, 9),
                                    activestyle="none", exportselection=False)
        self.clue_list.pack(fill=tk.X)
        self.clue_list.bind("<<ListboxSelect>>", self.on_clue_select)

        tk.Label(side, text="Thông báo:", font=(FONT, 10, "bold"),
                 bg=COLOR["bg"]).pack(anchor="w", pady=(10, 2))
        log_frame = tk.Frame(side)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log = tk.Text(log_frame, width=52, height=14, wrap=tk.WORD, font=(FONT, 9),
                           state=tk.DISABLED)
        scroll = tk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for kind, color in MSG_COLOR.items():
            self.log.tag_configure(kind, foreground=color)

        # ---- thanh trạng thái ----
        self.status_var = tk.StringVar()
        tk.Label(r, textvariable=self.status_var, anchor="w", font=(FONT, 9), bg="#ececec",
                 relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X)

        # ---- phím tắt ----
        r.bind("<Key-c>", lambda e: self.on_verdict(Status.CRIMINAL))
        r.bind("<Key-i>", lambda e: self.on_verdict(Status.INNOCENT))
        r.bind("<Key-h>", lambda e: self.on_hint())
        r.bind("<Key-r>", lambda e: self.on_restart())
        r.bind("<Control-o>", lambda e: self.on_load())

    # ================================================================ vẽ
    def _layout(self) -> tuple[int, int, int]:
        """(n, card_w, card_h): kích thước thẻ co giãn theo cửa sổ."""
        n = self.ctl.state().size
        w = max(self.canvas.winfo_width(), 300)
        h = max(self.canvas.winfo_height(), 300)
        card = max(90, min((w - HEADER) // n, (h - HEADER) // n))
        return n, card, card

    def draw_grid(self) -> None:
        cv = self.canvas
        cv.delete("all")
        if not self.ctl.loaded:
            cv.create_text(20, 20, anchor="nw", font=(FONT, 12), fill="#666",
                           text="Bấm 📂 Load để mở một file puzzle (.json).")
            return
        n, cw, ch = self._layout()
        hl = self.ctl.highlight()
        # tọa độ cột (A, B, C...) và hàng (1, 2, 3...)
        for i in range(n):
            cv.create_text(HEADER + i * cw + cw / 2, HEADER / 2, text=chr(ord("A") + i),
                           font=(FONT, 11, "bold"))
            cv.create_text(HEADER / 2, HEADER + i * ch + ch / 2, text=str(i + 1),
                           font=(FONT, 11, "bold"))
        for v in self.ctl.cells():
            self._draw_card(v, HEADER + (v.col - 1) * cw, HEADER + (v.row - 1) * ch, cw, ch, hl)

    def _draw_card(self, v: CellView, x: int, y: int, w: int, h: int, hl) -> None:
        cv = self.canvas
        x0, y0, x1, y1 = x + PAD / 2, y + PAD / 2, x + w - PAD / 2, y + h - PAD / 2
        if v.status == Status.CRIMINAL:
            fill, txt, label = COLOR["criminal"], COLOR["criminal_text"], "TỘI PHẠM"
        elif v.status == Status.INNOCENT:
            fill, txt, label = COLOR["innocent"], COLOR["innocent_text"], "VÔ TỘI"
        else:
            fill, txt, label = COLOR["facedown"], COLOR["facedown_text"], "?  (thẻ úp)"
        cv.create_rectangle(x0, y0, x1, y1, fill=fill, outline=COLOR["border"], width=1)

        # viền tô sáng (clue đang chọn) — vẽ bên trong thẻ
        if v.cell in hl.counted:
            cv.create_rectangle(x0 + 3, y0 + 3, x1 - 3, y1 - 3, outline=COLOR["counted"], width=4)
        elif v.cell in hl.anchors:
            cv.create_rectangle(x0 + 3, y0 + 3, x1 - 3, y1 - 3, outline=COLOR["counted"],
                                width=2, dash=(4, 3))
        # viền ô gợi ý / ô đang chọn — vẽ bên ngoài
        if v.cell == self.ctl.hint_cell:
            cv.create_rectangle(x0 - 2, y0 - 2, x1 + 2, y1 + 2, outline=COLOR["hint"], width=4)
        if v.cell == self.ctl.selected_cell:
            cv.create_rectangle(x0 - 1, y0 - 1, x1 + 1, y1 + 1, outline=COLOR["selected"], width=3)

        cx, inner = (x0 + x1) / 2, (x1 - x0) - 12
        compact = w < 130                      # lưới 5x5 / cửa sổ nhỏ -> chữ sát hơn
        small = 8 if compact else 9
        y_name, y_prof, y_label, y_clue = (18, 31, 44, 55) if compact else (22, 40, 56, 68)
        cv.create_text(x0 + 5, y0 + 4, anchor="nw", text=v.cell, font=(FONT, small, "bold"), fill="#555")
        if v.cell == self.ctl.hint_cell:
            cv.create_text(x1 - 5, y0 + 4, anchor="ne", text="💡", font=(FONT, small))
        cv.create_text(cx, y0 + y_name, text=v.name, font=(FONT, small + 3, "bold"),
                       fill="#222" if v.face_up else txt)
        cv.create_text(cx, y0 + y_prof, text=v.profession, font=(FONT, small), fill="#666")
        cv.create_text(cx, y0 + y_label, text=label, font=(FONT, small, "bold"), fill=txt)
        if v.clue_text:
            cv.create_text(cx, y0 + y_clue, anchor="n", text=v.clue_text, width=inner,
                           font=(FONT, small - 1 if compact else small), fill="#222", justify=tk.CENTER)

    def refresh(self) -> None:
        """Vẽ lại mọi thứ theo trạng thái hiện tại của controller."""
        self.title_var.set(self.ctl.title())
        if self.ctl.loaded and self.ctl.selected_cell:
            v = next(c for c in self.ctl.cells() if c.cell == self.ctl.selected_cell)
            st = {Status.CRIMINAL: "TỘI PHẠM", Status.INNOCENT: "VÔ TỘI"}.get(v.status, "chưa biết")
            self.sel_var.set(f"Ô đang chọn: {v.cell} — {v.name} ({v.profession}) — {st}")
        else:
            self.sel_var.set("Ô đang chọn: (bấm vào một thẻ trên lưới)")

        self.clue_list.delete(0, tk.END)
        self._clue_ids = []
        if self.ctl.loaded:
            for i, cv in enumerate(self.ctl.revealed_clues()):
                self.clue_list.insert(tk.END, f"[{cv.owner}] {cv.text}")
                self._clue_ids.append(cv.clue_id)
                if cv.clue_id == self.ctl.selected_clue_id:
                    self.clue_list.selection_set(i)
                    self.clue_list.see(i)
        legend = "Màu: đỏ = tội phạm, xanh = vô tội, xám = thẻ úp, viền cam = ô clue nhắc tới, viền tím = gợi ý"
        self.status_var.set(f"{self.ctl.classifier_label()}   |   {legend}")
        self.draw_grid()

    def show(self, msg: Message) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, msg.text + "\n", msg.kind)
        for line in msg.details:
            self.log.insert(tk.END, "   " + line + "\n", "info")
        self.log.insert(tk.END, "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _do(self, msg: Message) -> None:
        self.show(msg)
        self.refresh()

    # ================================================================ sự kiện
    def on_load(self) -> None:
        path = filedialog.askopenfilename(title="Chọn file puzzle", initialdir=_puzzles_dir(),
                                          filetypes=[("Puzzle JSON", "*.json"), ("Tất cả", "*.*")])
        if path:
            self._do(self.ctl.load(path))

    def on_restart(self) -> None:
        self._do(self.ctl.restart())

    def on_hint(self) -> None:
        self._do(self.ctl.hint())

    def on_auto_solve(self) -> None:
        self._do(self.ctl.auto_solve())

    def on_verdict(self, status: Status) -> None:
        self._do(self.ctl.submit(status))

    def on_canvas_click(self, event) -> None:
        if not self.ctl.loaded:
            return
        n, cw, ch = self._layout()
        col = int((event.x - HEADER) // cw) + 1
        row = int((event.y - HEADER) // ch) + 1
        if not (1 <= row <= n and 1 <= col <= n) or event.x < HEADER or event.y < HEADER:
            return
        cell = f"{chr(ord('A') + col - 1)}{row}"
        self.ctl.select_cell(cell)
        # bấm vào thẻ đã lật -> tô sáng luôn clue của thẻ đó
        v = next(c for c in self.ctl.cells() if c.cell == cell)
        if v.clue_id and v.clue_id != self.ctl.selected_clue_id:
            self.ctl.select_clue(v.clue_id)
        self.refresh()

    def on_clue_select(self, event=None) -> None:
        sel = self.clue_list.curselection()
        if sel:
            self.ctl.select_clue(self._clue_ids[sel[0]])
        self.refresh()


def run_gui(path: str | None = None) -> None:
    root = tk.Tk()
    root.geometry("1040x700")
    root.minsize(860, 560)
    app = GriductiveApp(root)
    if path:
        app._do(app.ctl.load(path))
    root.mainloop()
