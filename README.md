# Griductive Solver (CSC14003 – Project 2)

No-guess Griductive solver: propositional logic + CNF encoding + DPLL tự cài đặt.

## Chạy
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py gui                       # chơi / auto-solve bằng GUI
python main.py solve puzzles/3x3/example_3x3.json
python main.py solve puzzles/2x2/agent_chain.json # demo trace Phần 4
python main.py experiments --timeout 60  # -> results/results.csv
pytest                                   # chạy test
```

## Kiến trúc
```
GUI ──► GameEngine (hidden solution, clue chưa lật)
            │ PublicState (chỉ clue đã lật + verdict đã chứng minh)
            ▼
     DeductiveAgent ──► CNFEncoder (logic/) ──► DPLL (solver/)
```
| Thư mục | Nội dung | Phụ trách |
|---|---|---|
| `core/`, `gui/` | models, engine, load puzzle, GUI | Phần 1 |
| `logic/` | variables, regions, clue, CNF encoder, evaluator | Phần 2 |
| `solver/` | DPLL | Phần 3 |
| `agent/` | classify, deduction loop, hint, trace, uniqueness | Phần 4 |
| `experiments/`, `integration.py`, `tests/` | tích hợp, thực nghiệm, báo cáo, video | Phần 5 |

Hợp đồng giữa các module nằm trong docstring đầu mỗi file; cấu trúc dữ liệu chung ở `core/models.py`.
Định dạng puzzle: `docs/puzzle_format.md`.
Chi tiết thuật toán, SAT trace, uniqueness check và kịch bản demo Phần 4:
`docs/report/part4_deductive_agent.md`.

## Thành viên
| MSSV | Họ tên | Phần | % hoàn thành |
|---|---|---|---|
| | | 1 | |
| | | 2 | |
| | | 3 | |
| | | 4 | |
| | | 5 | |
