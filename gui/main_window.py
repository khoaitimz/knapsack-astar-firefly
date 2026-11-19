"""Graphical User Interface and background Worker for 0/1 Knapsack.

Responsible member: TV4

Architectural Separation:
- SolverWorker (QThread): executes algorithms in the background to prevent UI freezing.
- KnapsackMainWindow (QMainWindow): pure view and controller.
  - Takes user inputs (problem generation, file loading, algorithm parameters).
  - Starts SolverWorker.
  - Displays results (SolutionResult, comparison tables, metrics).
"""

from __future__ import annotations

import sys
from typing import Any

from algorithms.astar import solve_astar
from algorithms.firefly import FireflyConfig, solve_firefly
from core.knapsack import KnapsackProblem, SolutionResult

# Optional PySide6 import guard to allow headless environments and testing
try:
    from PySide6.QtCore import QObject, QThread, Signal
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

    # Minimal fallback stubs for testing without GUI dependencies installed
    class QObject:  # type: ignore
        pass

    class QThread:  # type: ignore
        def __init__(self, parent: Any = None) -> None:
            pass

        def start(self) -> None:
            pass

    class Signal:  # type: ignore
        def __init__(self, *types: Any) -> None:
            pass

        def emit(self, *args: Any) -> None:
            pass

        def connect(self, slot: Any) -> None:
            pass

    class QMainWindow:  # type: ignore
        def __init__(self, parent: Any = None) -> None:
            pass


class SolverWorker(QThread):
    """Background thread worker to execute Knapsack solvers asynchronously.

    Signals:
        finished: Emits SolutionResult upon successful run.
        error: Emits error message string upon exception.
    """

    if PYSIDE6_AVAILABLE:
        finished = Signal(SolutionResult)
        error = Signal(str)
    else:
        finished = Signal(object)
        error = Signal(str)

    def __init__(
        self,
        problem: KnapsackProblem,
        algorithm: str = "astar",
        firefly_config: FireflyConfig | None = None,
        astar_time_limit_sec: float = 5.0,
        astar_max_expanded_nodes: int = 100_000,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.problem = problem
        self.algorithm = algorithm
        self.firefly_config = firefly_config
        self.astar_time_limit_sec = astar_time_limit_sec
        self.astar_max_expanded_nodes = astar_max_expanded_nodes

    def run(self) -> None:
        """Executes the selected algorithm in background thread."""
        try:
            if self.algorithm == "astar":
                result = solve_astar(
                    problem=self.problem,
                    time_limit_sec=self.astar_time_limit_sec,
                    max_expanded_nodes=self.astar_max_expanded_nodes,
                )
            elif self.algorithm == "firefly":
                result = solve_firefly(
                    problem=self.problem,
                    config=self.firefly_config,
                )
            else:
                raise ValueError(f"Unknown algorithm: {self.algorithm}")

            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class KnapsackMainWindow(QMainWindow):
    """Main application window for Knapsack AI visual solver."""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.problem: KnapsackProblem | None = None
        self.worker: SolverWorker | None = None
        self.init_ui()

    def init_ui(self) -> None:
        """Initializes UI layout and widgets."""
        if not PYSIDE6_AVAILABLE:
            return

        self.setWindowTitle("0/1 Knapsack Solver - A* Search & Firefly Algorithm")
        self.resize(900, 650)

        # Central widget and layout skeleton
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)

        title_label = QLabel("0/1 Knapsack AI Solver (A* Search & Firefly Algorithm)")
        layout.addWidget(title_label)

        self.setCentralWidget(central_widget)

    def set_problem(self, problem: KnapsackProblem) -> None:
        """Attaches a problem instance to the GUI view."""
        self.problem = problem

    def run_solver(self, algorithm: str) -> None:
        """Spawns background SolverWorker to execute algorithm."""
        if self.problem is None:
            return
        self.worker = SolverWorker(
            problem=self.problem,
            algorithm=algorithm,
        )
        self.worker.finished.connect(self.on_solver_finished)
        self.worker.error.connect(self.on_solver_error)
        self.worker.start()

    def on_solver_finished(self, result: SolutionResult) -> None:
        """Slot called when worker finishes computation."""
        pass

    def on_solver_error(self, message: str) -> None:
        """Slot called when worker encounters an error."""
        pass
