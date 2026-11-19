"""Entry point: python main.py [gui|solve|experiments] ..."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def main() -> None:
    p = argparse.ArgumentParser(description="Griductive Solver")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("gui", help="Mở giao diện chơi game")
    s = sub.add_parser("solve", help="Giải 1 puzzle bằng agent (CLI)")
    s.add_argument("puzzle")
    e = sub.add_parser("experiments", help="Chạy toàn bộ test case")
    e.add_argument("--timeout", type=float, default=60.0)
    args = p.parse_args()

    if args.cmd in (None, "gui"):
        from griductive.gui.app import run_gui
        run_gui()
    elif args.cmd == "solve":
        from griductive.integration import solve_file
        solve_file(args.puzzle)
    elif args.cmd == "experiments":
        from griductive.experiments.run_experiments import run_all
        run_all(timeout=args.timeout)


if __name__ == "__main__":
    main()
