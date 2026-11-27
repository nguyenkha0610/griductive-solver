# Phần 4 — Deductive Logic Agent

## Mục tiêu và ranh giới thông tin

`DeductiveAgent` chỉ nhận `PublicState`: kích thước bàn, danh sách nhân vật,
manh mối đã lật và các trạng thái đã được chứng minh. Agent không đọc đáp án
ẩn hoặc clue của thẻ úp. Mỗi lần suy luận, `build_kb()` mã hóa các clue công
khai và trạng thái đã chứng minh thành CNF; các biến nhân vật là biến chính,
còn biến phụ chỉ phục vụ bộ đếm tuần tự, parity hoặc phép so sánh vùng.

## Kiểm tra hệ quả logic

Ký hiệu `C_i` là mệnh đề “nhân vật i là CRIMINAL”. Agent trước hết kiểm tra
tính nhất quán của `KB_t`. Nếu `KB_t` UNSAT thì trả `INCONSISTENT`, không suy
ra trạng thái từ một tri thức mâu thuẫn. Nếu KB nhất quán, agent chạy hai SAT
query có giả định tạm thời:

| Query | Kết quả | Kết luận |
|---|---|---|
| `KB_t AND NOT C_i` | UNSAT | `CRIMINAL` (chỉ trạng thái này còn khả thi) |
| `KB_t AND C_i` | UNSAT | `INNOCENT` |
| Cả hai query | SAT | `UNKNOWN` |

Đây là kiểm tra entailment bằng phản chứng: `KB_t entails C_i` đúng khi và chỉ
khi `KB_t AND NOT C_i` không có mô hình. Agent không chọn một mô hình SAT rồi
coi các giá trị tùy ý trong mô hình đó là kết luận; chỉ chấp nhận trạng thái bị
ép buộc bởi KB.

## Vòng lặp suy diễn và trace

`hint(state)` trả về nhân vật chưa lật đầu tiên theo thứ tự hàng-rồi-cột có
trạng thái được chứng minh, hoặc `None` nếu chưa có kết luận. `auto_solve(engine)`
thực hiện một lượt:

1. Chụp `PublicState` và kiểm tra KB nhất quán.
2. Thử cả hai giả định cho từng nhân vật chưa giải, theo thứ tự hàng-rồi-cột.
3. Nếu không có trạng thái bị ép buộc, kết thúc `STUCK`.
4. Gửi đúng một verdict đã chứng minh tới GameEngine. Khi được chấp nhận,
   engine lật thẻ và clue mới xuất hiện trong trạng thái công khai của lượt sau.
5. Lặp đến khi puzzle giải xong (`SOLVED`) hoặc KB mâu thuẫn (`INCONSISTENT`).

Mỗi `TraceStep` giữ số bước, clue ID đang hoạt động, các SAT query cùng kết
quả và số liệu DPLL (decisions, propagations, backtracks, runtime), verdict và
clue ID mới được lật. `DeductionTrace.to_dict()` xuất dữ liệu JSON-serializable.
Chạy demo CLI và xem trace đầy đủ:

```powershell
py main.py solve puzzles/2x2/agent_chain.json
```

`puzzles/2x2/agent_chain.json` là fixture demo kết thúc `SOLVED`. Puzzle
`3x3/example_3x3.json` có thể kết thúc `STUCK`: uniqueness của tập clue đầy đủ
không đồng nghĩa rằng clue đã lật đủ để suy ra mọi ô.

## Kiểm tra tính duy nhất

`count_solutions(all_clues, characters_state, limit=2)` giải toàn bộ clue set,
sau mỗi mô hình thêm blocking clause chỉ trên biến chính của nhân vật. Việc
không chặn biến phụ tránh đếm một cấu hình nhân vật nhiều lần do các cách gán
auxiliary khác nhau. Giá trị trả về bị chặn bởi `limit`; mặc định phân biệt
`0`, `1` và `2` (hai hoặc nhiều nghiệm). `check_uniqueness(...)` trả `True`
chính xác khi số nghiệm là một.

## Mã hóa clue dùng trong agent

Agent dùng cùng CNF encoder và DPLL trong project. Bộ đếm tuần tự mã hóa
`EXACTLY`, `AT_LEAST` và `AT_MOST`; `PARITY` dùng chuỗi XOR Tseitin. Clue
`COMPARE` hỗ trợ `extra.region_a`, `extra.region_b` (mỗi vùng theo định dạng
`Region`) và `extra.operator` là `"="`, `">"` hoặc `"<"`. Bộ semantic evaluator
được kiểm tra chéo với CNF trên tất cả phép gán của fixture 2×2.

## Kịch bản quay demo (5–10 phút)

1. Giới thiệu bàn chơi, nhân vật và các clue đang lật; nêu rõ agent chỉ nhận
   public state.
2. Chạy `py main.py solve puzzles/3x3/example_3x3.json`, chỉ cách đọc từng bước,
   clue ID, hai SAT assumptions, kết quả và thống kê DPLL.
3. Giải thích entailment bằng hai phép thử `KB AND NOT C_i` và `KB AND C_i`;
   phân biệt `CRIMINAL`, `INNOCENT`, `UNKNOWN` và `INCONSISTENT`.
4. Trình bày thứ tự chọn verdict, cập nhật clue giữa các lượt và các terminal
   state `SOLVED` / `STUCK` / `INCONSISTENT`.
5. Chạy kiểm tra uniqueness trong Python hoặc unit tests để minh họa blocking
   clause và phân biệt một nghiệm với nhiều nghiệm.

Tài liệu này chuẩn bị nội dung và lệnh chạy demo; video phải được quay và tải
lên Drive bởi thành viên có quyền truy cập ứng dụng/Drive. Không có link video
được đính kèm trong source.
