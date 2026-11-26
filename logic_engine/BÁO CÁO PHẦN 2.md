# BÁO CÁO PHẦN 2: LOGICAL REPRESENTATION & CNF ENCODING

Module cài đặt: `logic_engine/` (`variables.py`, `regions.py`, `clues.py`, `cnf_encoder.py`, `semantic_eval.py`, `stats.py`)

## 1. Biểu diễn Logic & Quản lý Biến (Boolean Variables)

### 1.1. Biến chính (Primary Variables)

Lưới có kích thước N × N, mỗi ô `(r, c)` chứa một nhân vật có đúng hai trạng thái. Mỗi ô được ánh xạ thành một biến Boolean duy nhất, đánh số từ 1 đến N²:

```
var(r, c) = r * N + c + 1        với 0 ≤ r, c < N
```

Quy ước ngữ nghĩa: biến nhận giá trị `True` khi nhân vật ở ô đó mang trạng thái "dương" (ví dụ: tội phạm), và `False` khi mang trạng thái "âm". Literal dương `+v` biểu diễn "ô mang trạng thái dương", literal âm `-v` biểu diễn điều ngược lại.

Ví dụ với N = 3:

| (r, c) | c = 0 | c = 1 | c = 2 |
| --- | --- | --- | --- |
| r = 0 | 1 | 2 | 3 |
| r = 1 | 4 | 5 | 6 |
| r = 2 | 7 | 8 | 9 |

Lớp `VariablePool` đảm nhiệm việc này: `var(cell)` trả về id của biến chính, `cell_of(var)` ánh xạ ngược.

### 1.2. Biến phụ (Auxiliary Variables)

Các clue dạng đếm (`EXACTLY`, `AT_LEAST`, `AT_MOST`, `BETWEEN`) và `PARITY` không thể viết trực tiếp thành một số ít mệnh đề CNF trên biến chính mà không bùng nổ số lượng mệnh đề. Vì vậy encoder cấp phát thêm các biến phụ thông qua `VariablePool.new_aux()`:

- Biến phụ được đánh số liên tiếp bắt đầu từ N² + 1, nên không bao giờ trùng với biến chính.
- Bộ đếm `num_aux` tăng mỗi lần cấp phát, phục vụ phần thống kê (mục 5).
- Mỗi clue có tập biến phụ riêng; các clue khác nhau không dùng chung biến phụ.
- Biến phụ chỉ là công cụ mã hóa. Chúng không mang ý nghĩa của bài toán và không xuất hiện trong lời giải cuối cùng.

Các biến phụ có hai vai trò:

1. **Bộ đếm tuần tự (sequential counter)** cho các ràng buộc đếm: biến `s[i][j]` mang nghĩa "trong i + 1 ô đầu của vùng có ít nhất j + 1 ô True".
2. **Biến XOR trung gian** cho `PARITY`: biến `t_i` mang nghĩa "tính chẵn lẻ của i ô đầu".

## 2. Quy tắc Mã hóa CNF (CNF Encoding Rules)

Ký hiệu: vùng của clue gồm m ô, `x1, ..., xm` là các literal tương ứng. Hàm `encode_clue` trước hết gọi `validate` để kiểm tra tham số, sau đó sinh danh sách mệnh đề.

### 2.1. Sáu loại Clue bắt buộc

**FACT** (ô duy nhất có giá trị `v`). Vùng phải có đúng 1 ô, `v` kiểu bool.

```
v = True  :  (x1)
v = False :  (¬x1)
```

Số mệnh đề: 1. Biến phụ: 0.

**SAME** (mọi ô trong vùng cùng giá trị). Với mọi cặp có thứ tự (a, b), a ≠ b, thêm mệnh đề `(¬a ∨ b)`, tức là a → b. Khi đó x1 → x2 → ... → x1 nên các ô buộc phải bằng nhau.

```
Số mệnh đề: m(m − 1). Biến phụ: 0.
```

**DIFFERENT** (vùng có cả ô True lẫn ô False, tức là không phải tất cả bằng nhau).

```
(x1 ∨ x2 ∨ ... ∨ xm)  ∧  (¬x1 ∨ ¬x2 ∨ ... ∨ ¬xm)
```

Với vùng 2 ô, đây chính xác là "hai ô khác nhau". Số mệnh đề: 2. Biến phụ: 0.

**AT\_MOST k** (số ô True ≤ k). Dùng mã hóa bộ đếm tuần tự của Sinz với các biến phụ `s[i][j]` (i = 1..m−1, j = 1..k):

```
(¬x1 ∨ s[1][1])
(¬s[1][j])                                   với j = 2..k
với i = 2..m−1:
    (¬xi ∨ s[i][1])
    (¬s[i−1][1] ∨ s[i][1])
    (¬xi ∨ ¬s[i−1][j−1] ∨ s[i][j])           với j = 2..k
    (¬s[i−1][j] ∨ s[i][j])                   với j = 2..k
    (¬xi ∨ ¬s[i−1][k])
(¬xm ∨ ¬s[m−1][k])
```

Trường hợp biên: k ≥ m thì ràng buộc luôn đúng (0 mệnh đề); k = 0 thì thêm `(¬xi)` cho mọi ô, không cần biến phụ.

```
Biến phụ (0 < k < m): (m − 1)·k
Số mệnh đề (0 < k < m): 2mk + m − 3k − 1
```

**AT\_LEAST k** (số ô True ≥ k). Quy về AT\_MOST bằng cách đảo dấu mọi literal:

```
Σ xi ≥ k   ⇔   Σ (¬xi) ≤ m − k
```

Nghĩa là AT\_LEAST k = AT\_MOST (m − k) trên các literal phủ định. Chi phí tính theo công thức AT\_MOST với k' = m − k.

**EXACTLY k** (số ô True = k). Hội của AT\_LEAST k và AT\_MOST k:

```
EXACTLY k = AT_LEAST k ∧ AT_MOST k
Biến phụ (0 < k < m): (m − 1)·m
```

### 2.2. Hai loại Clue mở rộng

**BETWEEN (lo, hi)** — số ô True nằm trong khoảng \[lo, hi\].

- Ngữ nghĩa: `lo ≤ Σ xi ≤ hi`, với điều kiện `0 ≤ lo ≤ hi ≤ m`.
- Biến đổi CNF: `BETWEEN(lo, hi) = AT_LEAST lo ∧ AT_MOST hi`. Nó khái quát EXACTLY (lo = hi) và dùng lại hai hàm mã hóa đã có.
- Chi phí: tổng chi phí của AT\_LEAST lo và AT\_MOST hi.

**PARITY p** — số ô True là chẵn (p = 0) hoặc lẻ (p = 1).

- Ngữ nghĩa: `(Σ xi) mod 2 = p`.
- Biến đổi CNF: dùng chuỗi XOR. Đặt `t1 = x1`. Với i = 2..m, cấp phát biến phụ `ti` sao cho `ti = t(i−1) ⊕ xi`, mã hóa bằng 4 mệnh đề:

```
(¬ti ∨  t(i−1) ∨  xi)
(¬ti ∨ ¬t(i−1) ∨ ¬xi)
( ti ∨ ¬t(i−1) ∨  xi)
( ti ∨  t(i−1) ∨ ¬xi)
```

Cuối cùng thêm unit clause `(tm)` nếu p = 1 hoặc `(¬tm)` nếu p = 0.

```
Biến phụ: m − 1
Số mệnh đề: 4(m − 1) + 1
```

### 2.3. Tổng hợp chi phí mã hóa (vùng m = 5 ô, k = 2)

Số liệu đo trực tiếp từ encoder:

| Clue | Biến phụ | Số mệnh đề |
| --- | --- | --- |
| FACT | 0 | 1 |
| SAME | 0 | 20 |
| DIFFERENT | 0 | 2 |
| EXACTLY 2 | 20 | 43 |
| AT\_LEAST 2 | 12 | 25 |
| AT\_MOST 2 | 8 | 18 |
| BETWEEN (1, 3) | 28 | 57 |
| PARITY 1 | 4 | 17 |

## 3. Định nghĩa Vùng (Region Definitions)

Vùng là một đối tượng `Region(kind, params)` bất biến. Hàm `get_cells(region, n)` trả về danh sách tọa độ `(r, c)` thuộc vùng trên lưới n × n.

| Loại vùng | Khai báo | Tập ô |
| --- | --- | --- |
| Hàng | `row(r)` | `{(r, c) : 0 ≤ c < N}` |
| Cột | `col(c)` | `{(r, c) : 0 ≤ r < N}` |
| Ô lân cận | `neighbors(r, c, diagonal=True)` | các ô `(r + dr, c + dc)` với `dr, dc ∈ {−1, 0, 1}`, `(dr, dc) ≠ (0, 0)`, nằm trong lưới |
| Danh sách tùy chỉnh | `custom([(r1, c1), ...])` | đúng các ô được liệt kê |

Ghi chú:

- Với `neighbors`, tham số `diagonal=True` lấy 8 hướng (tối đa 8 ô); `diagonal=False` chỉ lấy 4 hướng ngang/dọc (tối đa 4 ô). Ô nằm ngoài lưới bị loại, nên ô ở góc có 3 (hoặc 2) lân cận và ô ở cạnh có 5 (hoặc 3). Chính ô trung tâm không thuộc vùng lân cận.
- Mọi vùng đều qua bước kiểm tra trong `clues.validate`: vùng không rỗng, không chứa ô trùng lặp, mọi ô nằm trong lưới.
- Kích thước vùng m quyết định chi phí mã hóa ở mục 2 (cụ thể là các công thức theo m và k).

## 4. CNF Encoder & Direct Semantic Evaluator

### 4.1. Luồng hoạt động của CNF Encoder

```
Clue ──► validate(clue, n) ──► get_cells ──► ánh xạ ô → literal (VariablePool)
     ──► sinh mệnh đề theo loại clue (cấp biến phụ nếu cần)
     ──► KnowledgeBase.clauses  (danh sách mệnh đề CNF)
```

1. `KnowledgeBase(n)` khởi tạo một `VariablePool` và danh sách mệnh đề rỗng.
2. `add_clue(clue)` gọi `encode_clue`, kết quả được nối vào KB. Mỗi mệnh đề là một danh sách số nguyên (DIMACS-style): số dương là literal dương, số âm là literal phủ định.
3. Việc kiểm tra tham số diễn ra trước khi sinh mệnh đề, nên clue sai (value ngoài khoảng, vùng ngoài lưới, FACT với vùng ≠ 1 ô, ...) bị từ chối bằng `ValueError`, không làm hỏng KB.

### 4.2. Cập nhật Knowledge Base bằng Unit Clauses

Khi một kết luận (verdict) về ô `(r, c)` đã được chứng minh, ta gọi `add_verdict(cell, value)`:

```
value = True  :  thêm [ var(cell) ]
value = False :  thêm [ −var(cell) ]
```

Đây là unit clause. Nó làm KB mạnh hơn: các bước unit propagation của bộ giải lập tức lan truyền giá trị đã biết sang các mệnh đề còn lại, giúp suy ra thêm kết luận mới. KB chỉ thêm mệnh đề (đơn điệu), không xóa mệnh đề đã có.

### 4.3. Direct Semantic Evaluator

`semantic_eval.evaluate(clue, assignment, n)` đánh giá clue trực tiếp trên một trạng thái đầy đủ `assignment: {(r, c): bool}`, **không** dùng CNF, biến phụ hay bộ giải SAT. Nó chỉ:

1. lấy danh sách ô của vùng,
2. đọc giá trị các ô từ `assignment`,
3. so sánh trực tiếp với định nghĩa ngữ nghĩa (ví dụ EXACTLY: `sum(vals) == k`; SAME: `len(set(vals)) == 1`; PARITY: `sum(vals) % 2 == p`).

**Nguyên lý kiểm tra độc lập.** Vì evaluator được viết tách biệt khỏi encoder nên nó đóng vai trò "oracle". Với mọi clue C và mọi trạng thái S của biến chính, phải có:

```
C thỏa mãn S (theo evaluator)   ⇔   tồn tại gán biến phụ sao cho CNF(C) thỏa mãn khi các biến chính lấy giá trị từ S
```

Vế phải được kiểm tra bằng một bộ giải DPLL nhỏ (chỉ dùng trong kiểm thử): cố định biến chính theo S, rồi hỏi bộ giải có tồn tại cách gán biến phụ hay không.

**Kết quả kiểm thử** (`test_engine.py`, lưới 3 × 3): 72 clue (đủ 8 loại, trên 5 vùng khác nhau: hàng, cột, lân cận 8 hướng, lân cận 4 hướng, danh sách tùy chỉnh) × 60 trạng thái ngẫu nhiên: **0 sai lệch** giữa encoder và evaluator.

## 5. Thống kê & Đánh giá Độ phức tạp

### 5.1. Công thức theo kích thước

- Biến chính: N².
- Biến phụ và số mệnh đề của từng clue phụ thuộc vào kích thước vùng m và tham số k theo mục 2. Cả hai đều tăng tuyến tính theo m và theo k, nên mỗi clue đếm tốn O(m·k) biến phụ và O(m·k) mệnh đề (so với mã hóa trực tiếp "cấm mọi tập k + 1 ô" cần C(m, k+1) mệnh đề).
- `SAME` tốn O(m²) mệnh đề nhưng không cần biến phụ.
- `PARITY` tốn O(m) biến phụ và O(m) mệnh đề.

### 5.2. Bảng số liệu theo kích thước puzzle

Hai kịch bản đo bằng `stats.collect_stats(kb)`:

- **Kịch bản A**: mỗi hàng và mỗi cột có một clue `EXACTLY N//2` (tổng 2N clue, vùng m = N).
- **Kịch bản B**: kịch bản A cộng thêm clue `AT_MOST 2` trên 8 ô lân cận của mỗi ô (thêm N² clue).

| N | Biến chính | Kịch bản A: biến phụ | Kịch bản A: mệnh đề | Kịch bản B: biến phụ | Kịch bản B: mệnh đề |
| --- | --- | --- | --- | --- | --- |
| 3 | 9 | 36 | 78 | 98 | 215 |
| 4 | 16 | 96 | 208 | 232 | 516 |
| 5 | 25 | 200 | 430 | 438 | 975 |
| 6 | 36 | 360 | 768 | 728 | 1616 |
| 7 | 49 | 588 | 1246 | 1114 | 2463 |
| 8 | 64 | 896 | 1888 | 1608 | 3540 |
| 9 | 81 | 1296 | 2718 | 2222 | 4871 |
| 10 | 100 | 1800 | 3760 | 2968 | 6480 |

Ví dụ kiểm tra công thức ở kịch bản A: với N = 4, k = 2, mỗi EXACTLY có (m − 1)·m = 12 biến phụ, 2N = 8 clue nên có 96 biến phụ, khớp bảng. Cũng với bộ đếm tuần tự, AT\_MOST(m, k) đo được: (m, k) = (3, 1) → 2 biến phụ, 5 mệnh đề; (5, 2) → 8, 18; (6, 3) → 15, 32; (8, 4) → 28, 59, đúng với công thức `(m − 1)k` và `2mk + m − 3k − 1`.

### 5.3. Nhận xét

- Ở kịch bản A, biến phụ tăng xấp xỉ O(N³) (2N clue × N² biến phụ mỗi clue), mệnh đề cũng tăng cùng bậc. Số biến chính chỉ là O(N²) nên biến phụ nhanh chóng chiếm đa số tổng số biến (N = 10: 1800 biến phụ so với 100 biến chính).
- Ở kịch bản B, các clue lân cận có m ≤ 8 và k = 2 nhỏ nên chi phí mỗi clue gần như hằng số (tối đa 14 biến phụ cho vùng 8 ô), tổng tăng theo O(N²).
- Bộ đếm tuần tự giữ kích thước CNF ở mức đa thức, phù hợp với các bộ giải SAT, đổi lại cần thêm biến phụ. Unit clauses từ verdict không làm tăng số biến mà chỉ thêm 1 mệnh đề mỗi kết luận.
