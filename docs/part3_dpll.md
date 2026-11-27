# Phần 3: Bộ giải SAT DPLL

## 1. Giới thiệu

Thuật toán Davis–Putnam–Logemann–Loveland (DPLL) là một thuật toán tìm kiếm
quay lui đầy đủ để quyết định tính thỏa mãn của các công thức mệnh đề ở dạng
chuẩn hội (Conjunctive Normal Form – CNF). Thuật toán liên tục rút gọn công
thức dựa trên một phép gán từng phần, phát hiện mâu thuẫn và phân nhánh trên
một biến chưa được gán khi các phép suy diễn xác định chưa đủ để kết luận.

Griductive Solver sử dụng các biến mệnh đề để biểu diễn trạng thái của các nhân
vật, sau đó chuyển những gợi ý đã được tiết lộ và các sự kiện đã chứng minh
thành CNF. DPLL xác định liệu tri thức công khai đó có nhất quán hay một giả
định tạm thời cho một ứng viên có thể đúng hay không. Bộ giải chỉ nhận cơ sở
tri thức đã mã hóa; nó không truy cập lời giải ẩn hoặc các gợi ý chưa được tiết
lộ trong game engine.

## 2. Biểu diễn CNF

Bộ giải sử dụng cách biểu diễn DIMACS do bộ mã hóa của Phần 2 tạo ra:

* Biến Boolean được biểu diễn bằng số nguyên dương (`1`, `2`, ...).
* Literal dương (`v`) nghĩa là biến `v` có giá trị đúng; literal âm (`-v`)
  nghĩa là biến đó có giá trị sai.
* Clause là một dãy literal, được hiểu là phép tuyển (OR).
* Công thức CNF là một dãy clause, được hiểu là phép hội (AND).

Ví dụ:

```python
cnf = [[1, 2], [-1, 3], [-2, -3]]
```

biểu diễn `(x1 OR x2) AND (NOT x1 OR x3) AND (NOT x2 OR NOT x3)`.
CNF rỗng luôn đúng, trong khi CNF chứa một clause rỗng luôn sai. Literal lặp
lại không làm thay đổi ý nghĩa; clause chứa đồng thời `v` và `-v` là hằng đúng
(tautology) và được bỏ qua khi tìm kiếm. Bộ giải kiểm tra mỗi literal là số
nguyên khác không và nằm trong phạm vi biến đã khai báo; dữ liệu CNF đầu vào
không bị sửa đổi.

## 3. Các thành phần của thuật toán

### Unit propagation

Với mỗi clause, bộ giải bỏ qua clause nếu một literal đã được gán khiến clause
đúng. Nếu không, bộ giải thu thập các literal chưa được gán. Khi chỉ còn đúng
một literal chưa được gán, literal đó bắt buộc phải đúng. Công thức được quét
lại sau mỗi phép gán bắt buộc và tiếp tục cho đến khi không còn unit clause.
Bộ đếm `propagations` tính mỗi phép gán mới được suy ra theo cách này, kể cả
trong nhánh thất bại; giả định đầu vào và quyết định phân nhánh không được tính
là propagation.

### Phát hiện mâu thuẫn

Nếu một clause không có literal nào đúng và cũng không còn literal nào chưa
được gán, clause đó sai dưới phép gán hiện tại. Bộ tìm kiếm lập tức kết luận
nhánh đó thất bại. Hai yêu cầu unit đối nghịch được phát hiện khi phép gán unit
thứ nhất khiến clause còn lại trở thành sai. Các giả định trái ngược nhau cũng
được kết luận là UNSAT trước khi bắt đầu tìm kiếm.

### Lựa chọn biến xác định

Sau khi propagation hoàn tất, bộ giải thu thập các biến chưa được gán xuất
hiện trong những clause chưa được thỏa mãn, rồi chọn biến có chỉ số nhỏ nhất.
Thuật toán không phân nhánh trên biến đã được gán hoặc biến chỉ xuất hiện
trong các clause đã được thỏa mãn.

### Phân nhánh đệ quy và quay lui

Biến được chọn trước tiên được gán `True`; nếu nhánh đó thất bại, bộ giải thử
`False`. Mỗi lời gọi con nhận một bản sao của phép gán hiện tại, do đó các phép
gán trong nhánh thất bại không thể ảnh hưởng đến nhánh kế tiếp. Nhánh tìm được
nghiệm trả về ngay. Nếu cả hai giá trị đều thất bại, lời gọi đệ quy hiện tại
trả về UNSAT.

### Thống kê

`decisions` đếm mỗi phép gán được thử trong quá trình phân nhánh (bao gồm cả
literal đối nghịch ở lần thử thứ hai). `propagations` đếm các phép gán mới suy
ra từ unit clause. `backtracks` đếm mỗi phép gán nhánh thất bại bị loại bỏ.
`runtime` là thời gian thực thi đo bằng `time.perf_counter()`. Khi kết quả là
SAT, model trả về chứa mọi biến từ `1` đến `num_vars`; các biến không cần thiết
để thỏa mãn công thức được hoàn thiện một cách xác định với giá trị `False`.

## 4. Mã giả

Mã giả dưới đây tương ứng với phần cài đặt, bao gồm thứ tự thử hai giá trị và
cách tính các thống kê:

```text
SOLVE(CNF, num_vars, assumptions):
    kiểm tra literal và phạm vi biến
    chuẩn hóa clause bằng cách loại literal trùng và tautology
    assignment := các phép gán từ assumptions
    nếu assumptions mâu thuẫn: trả về UNSAT
    model := SEARCH(assignment)
    trả về SAT(model) nếu tìm thấy model, ngược lại trả về UNSAT

SEARCH(assignment):
    lặp:
        tìm clause đầu tiên chưa được thỏa mãn
        nếu clause không còn literal chưa gán: trả về thất bại (mâu thuẫn)
        nếu clause chỉ còn một literal chưa gán:
            gán literal đó; tăng propagations
        ngược lại:
            kết thúc propagation

    variables := các biến chưa gán trong những clause chưa thỏa mãn
    nếu variables rỗng:
        gán False cho các biến chưa có giá trị trong 1..num_vars
        trả về phép gán hoàn chỉnh

    variable := biến nhỏ nhất trong variables
    với value lần lượt là [True, False]:
        tăng decisions
        child := bản sao assignment với variable := value
        model := SEARCH(child)
        nếu tìm thấy model: trả về model
        tăng backtracks
    trả về thất bại
```

## 5. Ví dụ minh họa

Xét công thức:

```text
CNF = [[-1, 2], [-1, -2], [1, 2]]
       (NOT x1 OR x2) AND (NOT x1 OR NOT x2) AND (x1 OR x2)
```

Ban đầu không có unit clause. Theo quy tắc xác định, bộ giải chọn `x1`.

1. Nhánh đầu tiên gán `x1 = True`.
2. Clause thứ nhất trở thành unit clause `[2]`; propagation gán `x2 = True`.
3. Clause thứ hai `[-1, -2]` lúc này sai, vì vậy nhánh hiện tại mâu thuẫn.
4. Bộ giải loại bỏ nhánh đó và thử `x1 = False`.
5. Clause thứ ba `[1, 2]` trở thành unit clause, nên propagation gán
   `x2 = True`. Các clause còn lại đều được thỏa mãn.
6. Kết quả là SAT với phép gán `{1: False, 2: True}`.

Ví dụ này được chạy trong `scripts/demo_dpll.py`. Theo quy ước đếm đã nêu,
trường hợp này có hai decisions, hai propagations và một backtrack. Runtime
phụ thuộc vào môi trường thực thi.

## 6. Phân tích độ phức tạp

Với `n` biến, cây tìm kiếm DPLL có trường hợp xấu nhất theo hàm mũ, tối đa
`O(2^n)` phép gán. Nếu quét trực tiếp toàn bộ literal trong CNF tại mỗi nút
tìm kiếm, cận trên thời gian là `O(2^n * L)`, trong đó `L` là tổng số lần xuất
hiện của literal. Độ sâu đệ quy tối đa là `n`. Do mỗi nhánh đệ quy sao chép
phép gán và giữ tập biến ứng viên cục bộ, bộ nhớ phụ trong trường hợp xấu nhất
là `O(n^2)`; công thức được lưu cần thêm `O(L)` bộ nhớ.

Với các puzzle Griductive nhỏ, unit propagation thường gán được nhiều biến
trước khi cần phân nhánh. Vì vậy, kích thước tìm kiếm thực tế có thể nhỏ hơn
nhiều so với trường hợp xấu nhất. Phiên bản này ưu tiên tính rõ ràng và hành
vi xác định thay vì các tối ưu hiệu năng nâng cao.

## 7. Kết quả thực nghiệm

Bộ test của repository bao gồm mười nhóm tình huống được yêu cầu và phép so
sánh với oracle bảng chân trị trên các công thức hai biến gồm tối đa ba clause
được chọn. Các trường hợp demo cũng cung cấp số liệu thực tế:

| Trường hợp | Kết quả dự kiến | Decisions | Propagations | Backtracks | Runtime |
|---|---:|---:|---:|---:|---:|
| Ví dụ SAT ở trên | SAT | 2 | 2 | 1 | 0.000047 giây |
| Công thức mâu thuẫn bốn clause trong demo | UNSAT | 2 | 2 | 2 | 0.000033 giây |

Các bộ đếm xác định trong bảng tuân theo định nghĩa ở trên. Runtime là số đo
từ một lần chạy trong môi trường hiện tại; giá trị có thể thay đổi theo phần
cứng và tải hệ thống. Demo đo và in runtime thực tế ở mỗi lần chạy.

## 8. Hạn chế

Phiên bản phục vụ mục đích giáo dục này sử dụng quay lui theo thứ tự thời gian,
quét lại các clause nhiều lần và luôn chọn biến đủ điều kiện có chỉ số nhỏ
nhất. Thuật toán chưa có loại bỏ literal thuần (pure-literal elimination),
propagation bằng watched literals, học mâu thuẫn, khởi động lại hoặc heuristic
phân nhánh nâng cao như VSIDS. Đây là những hướng có thể cải tiến nếu CNF của
puzzle lớn khiến quá trình tìm kiếm tốn nhiều thời gian.

## 9. Giao diện tích hợp

Bộ giải hỗ trợ cả hàm theo hợp đồng của Phần 3 và lớp có thể tái sử dụng:

```python
from griductive.solver.dpll import DPLLSolver, solve

result = solve(kb.clauses, kb.num_vars)
# hoặc để bộ giải tự suy ra số biến:
result = DPLLSolver().solve(cnf)

if result.status == "SAT":
    model = result.assignment
```

Phần 4 có thể kiểm tra trạng thái một ứng viên bằng cách thêm một giả định
literal tạm thời. Nếu `variable` là mã biến chính của một ô, dùng `variable`
để kiểm tra giá trị `True` và `-variable` để kiểm tra giá trị `False`:

```python
candidate = solve(kb.clauses, kb.num_vars, assumptions=[variable])
opposite = solve(kb.clauses, kb.num_vars, assumptions=[-variable])
```

Các giả định không được nối thêm vào hoặc ghi đè lên `kb.clauses`. Phần 4 có
thể phân loại ứng viên dựa trên kết quả SAT/UNSAT từ hai lần gọi độc lập này.
Bộ mã hóa cần tiếp tục tạo cơ sở tri thức chỉ từ `PublicState` được cung cấp;
DPLL không nhận dữ liệu về lời giải ẩn.
