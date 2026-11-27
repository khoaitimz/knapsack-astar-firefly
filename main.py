"""Main entry point for 0/1 Knapsack AI project.

Responsible member: TV2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from algorithms.astar import solve_astar
from core.dataset import generate_dataset, load_dataset_csv, load_dataset_json
from core.knapsack import Item, KnapsackProblem, SolutionResult


def run_cli_demo(
    problem: KnapsackProblem | None = None,
    time_limit_sec: float = 5.0,
    max_expanded_nodes: int = 100_000,
) -> SolutionResult:
    """Solve a supplied problem (or the built-in sample) and print its result."""
    print("=" * 60)
    print("0/1 Knapsack Solver Project (A* Search & Firefly Algorithm)")
    print("=" * 60)

    if problem is None:
        problem = KnapsackProblem(
            items=[
                Item(value=24.0, weight=12.0, id="item_a"),
                Item(value=13.0, weight=7.0, id="item_b"),
                Item(value=23.0, weight=11.0, id="item_c"),
                Item(value=15.0, weight=8.0, id="item_d"),
            ],
            capacity=20.0,
            name="sample_cli_01",
        )

    print(f"Loaded problem instance : '{problem.name}'")
    print(f"Total items             : {problem.num_items}")
    print(f"Knapsack capacity       : {problem.capacity}")
    print(f"Total potential value   : {problem.total_value}")
    print(f"Total potential weight  : {problem.total_weight}")
    print("-" * 60)
    result = solve_astar(problem, time_limit_sec, max_expanded_nodes)
    print(f"Algorithm               : {result.algorithm_name}")
    print(f"Status                  : {result.status}")
    print(f"Selected indices (0-based): {result.selected_indices}")
    print(f"Selected item IDs       : {[problem[i].id for i in result.selected_indices]}")
    print(f"Binary vector           : {result.binary_vector}")
    print(f"Total value             : {result.total_value}")
    print(f"Total weight            : {result.total_weight}")
    print(f"Feasible                : {result.is_feasible}")
    print(f"Execution time (ms)     : {result.execution_time_ms:.3f}")
    print(f"Expanded nodes          : {result.metrics['expanded_nodes']}")
    print(f"Generated nodes         : {result.metrics['generated_nodes']}")
    print(f"Pruned nodes            : {result.metrics['pruned_nodes']}")
    print("=" * 60)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Launch the GUI by default, or run A* through the explicit CLI mode."""
    parser = argparse.ArgumentParser(
        description="0/1 Knapsack: A* Search & Firefly Algorithm",
        epilog="Example: python main.py --cli --dataset assets/datasets/sample_01.json",
    )
    parser.add_argument("--cli", action="store_true", help="run A* without opening the GUI")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--dataset", type=Path, help="load a JSON or CSV dataset (CLI mode)")
    source.add_argument("--n-items", type=int, help="generate this many items (CLI mode)")
    parser.add_argument(
        "--capacity-ratio", type=float, default=0.5,
        help="capacity / total weight for generated data (default: 0.5)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="random seed for generated data (default: 42)",
    )
    parser.add_argument(
        "--time-limit", type=float, default=5.0,
        help="A* time limit in seconds (default: 5)",
    )
    parser.add_argument(
        "--max-expanded-nodes", type=int, default=100_000,
        help="A* expansion limit (default: 100000)",
    )
    args = parser.parse_args(argv)

    # Loading/generating a dataset also explicitly selects the CLI. Optional GUI
    # dependencies are imported only after choosing the application mode.
    cli_mode = args.cli or args.dataset is not None or args.n_items is not None
    if not cli_mode:
        try:
            from PySide6.QtWidgets import QApplication
            from gui.main_window import KnapsackMainWindow
        except ImportError:
            print("[Notice] PySide6 unavailable. Running CLI mode:")
        else:
            app = QApplication([sys.argv[0]])
            window = KnapsackMainWindow()
            window.show()
            return app.exec()

    try:
        problem = None
        if args.dataset is not None:
            extension = args.dataset.suffix.lower()
            if extension == ".json":
                problem = load_dataset_json(str(args.dataset))
            elif extension == ".csv":
                problem = load_dataset_csv(str(args.dataset))
            else:
                raise ValueError("Dataset must be a .json or .csv file.")
        elif args.n_items is not None:
            problem = generate_dataset(
                n_items=args.n_items,
                capacity_ratio=args.capacity_ratio,
                seed=args.seed,
            )
        run_cli_demo(problem, args.time_limit, args.max_expanded_nodes)
    except (ValueError, OSError) as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
