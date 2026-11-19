"""Main entry point for 0/1 Knapsack AI project.

Responsible member: TV2
"""

from __future__ import annotations

import sys

from core.dataset import generate_dataset
from core.knapsack import Item, KnapsackProblem


def run_cli_demo() -> None:
    """Runs a quick CLI demonstration verifying project setup and interfaces."""
    print("=" * 60)
    print("0/1 Knapsack Solver Project (A* Search & Firefly Algorithm)")
    print("=" * 60)

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
    print("Interface contracts initialized successfully.")
    print("Algorithms are ready for implementation by TV2 (A*) and TV3 (Firefly).")
    print("=" * 60)


def main() -> int:
    """Application entry point."""
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import KnapsackMainWindow

        app = QApplication(sys.argv)
        window = KnapsackMainWindow()
        window.show()
        return app.exec()
    except ImportError:
        print("[Notice] PySide6 not installed in current environment. Running CLI mode:")
        run_cli_demo()
        return 0


if __name__ == "__main__":
    sys.exit(main())
