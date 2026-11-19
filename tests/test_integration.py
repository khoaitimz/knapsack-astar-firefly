"""Integration tests verifying cross-module imports, contracts, and benchmark pipeline.

Responsible member: TV4
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from algorithms.astar import solve_astar
from algorithms.firefly import FireflyConfig, solve_firefly
from core.dataset import generate_dataset
from core.evaluation import compute_upper_bound, evaluate_binary_solution, repair_solution
from core.knapsack import Item, KnapsackProblem, SolutionResult
from experiments.benchmark import export_benchmark_results, run_benchmark
from gui.main_window import KnapsackMainWindow, SolverWorker


class TestCrossModuleImports(unittest.TestCase):
    """Verifies that all project packages import cleanly without circular dependencies."""

    def test_imports_and_types(self) -> None:
        self.assertTrue(callable(solve_astar))
        self.assertTrue(callable(solve_firefly))
        self.assertTrue(callable(run_benchmark))
        self.assertTrue(callable(export_benchmark_results))
        self.assertTrue(issubclass(SolverWorker, object))
        self.assertTrue(issubclass(KnapsackMainWindow, object))


class TestBenchmarkPipeline(unittest.TestCase):
    """Tests the benchmark execution framework and export functionality."""

    def setUp(self) -> None:
        self.problem = KnapsackProblem(
            items=[
                Item(value=10.0, weight=5.0, id="item_0"),
                Item(value=20.0, weight=8.0, id="item_1"),
            ],
            capacity=10.0,
            name="integration_prob",
        )

    def test_run_benchmark_and_export(self) -> None:
        records = run_benchmark(
            problems=[self.problem],
            firefly_config=FireflyConfig(population_size=10, max_iterations=5, seed=123),
            fa_runs=2,
            astar_time_limit_sec=1.0,
            astar_max_expanded_nodes=100,
        )

        # Expect 1 A* record + 2 Firefly records = 3 records
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["algorithm"], "astar")
        self.assertEqual(records[1]["algorithm"], "firefly")
        self.assertEqual(records[2]["algorithm"], "firefly")

        # Test export to temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_benchmark_results(records, output_dir=tmpdir)
            self.assertTrue(Path(paths["csv_path"]).exists())
            self.assertTrue(Path(paths["json_path"]).exists())
            self.assertGreater(Path(paths["csv_path"]).stat().st_size, 0)
            self.assertGreater(Path(paths["json_path"]).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
