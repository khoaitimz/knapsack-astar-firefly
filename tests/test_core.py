"""Unit tests for core models, dataset handlers, and evaluation logic.

Responsible member: TV1
"""

from __future__ import annotations

import math
from pathlib import Path
import unittest

from core.dataset import (
    generate_dataset,
    load_dataset_csv,
    load_dataset_json,
    validate_problem,
)
from core.evaluation import (
    compute_upper_bound,
    evaluate_binary_solution,
    repair_solution,
)
from core.knapsack import (
    Item,
    KnapsackProblem,
    SolutionResult,
    VALID_SOLUTION_STATUSES,
)


class TestItem(unittest.TestCase):
    """Tests for Item dataclass validation and properties."""

    def test_valid_item(self) -> None:
        item = Item(value=10.0, weight=5.0, id="it_1")
        self.assertEqual(item.value, 10.0)
        self.assertEqual(item.weight, 5.0)
        self.assertEqual(item.id, "it_1")
        self.assertEqual(item.density, 2.0)

    def test_zero_or_negative_weight_raises(self) -> None:
        with self.assertRaises(ValueError):
            Item(value=10.0, weight=0.0)
        with self.assertRaises(ValueError):
            Item(value=10.0, weight=-2.0)

    def test_negative_value_raises(self) -> None:
        with self.assertRaises(ValueError):
            Item(value=-1.0, weight=5.0)

    def test_non_finite_raises(self) -> None:
        with self.assertRaises(ValueError):
            Item(value=float("inf"), weight=5.0)
        with self.assertRaises(ValueError):
            Item(value=10.0, weight=float("nan"))


class TestKnapsackProblem(unittest.TestCase):
    """Tests for KnapsackProblem initialization and automatic ID assignment."""

    def test_valid_problem_and_auto_ids(self) -> None:
        items = [
            Item(value=10.0, weight=5.0),
            Item(value=20.0, weight=8.0, id="custom_id"),
            Item(value=15.0, weight=6.0, id=""),
        ]
        prob = KnapsackProblem(items=items, capacity=12.0, name="test_prob")
        self.assertEqual(prob.num_items, 3)
        self.assertEqual(prob.capacity, 12.0)
        self.assertEqual(prob.name, "test_prob")
        self.assertEqual(prob.items[0].id, "item_0")
        self.assertEqual(prob.items[1].id, "custom_id")
        self.assertEqual(prob.items[2].id, "item_2")
        self.assertEqual(prob.total_value, 45.0)
        self.assertEqual(prob.total_weight, 19.0)

    def test_empty_items_raises(self) -> None:
        with self.assertRaises(ValueError):
            KnapsackProblem(items=[], capacity=10.0)

    def test_invalid_capacity_raises(self) -> None:
        items = [Item(value=10.0, weight=5.0)]
        with self.assertRaises(ValueError):
            KnapsackProblem(items=items, capacity=0.0)
        with self.assertRaises(ValueError):
            KnapsackProblem(items=items, capacity=-5.0)
        with self.assertRaises(ValueError):
            KnapsackProblem(items=items, capacity=float("inf"))


class TestSolutionResult(unittest.TestCase):
    """Tests for SolutionResult validation."""

    def test_valid_result(self) -> None:
        res = SolutionResult(
            algorithm_name="test_algo",
            selected_indices=[0, 1],
            binary_vector=[1, 1, 0],
            total_value=30.0,
            total_weight=13.0,
            is_feasible=True,
            execution_time_ms=1.5,
            status="optimal",
            metrics={"expanded_nodes": 12},
        )
        self.assertEqual(res.status, "optimal")
        self.assertTrue(res.is_feasible)

    def test_invalid_status_raises(self) -> None:
        with self.assertRaises(ValueError):
            SolutionResult(
                algorithm_name="test_algo",
                selected_indices=[0],
                binary_vector=[1],
                total_value=10.0,
                total_weight=5.0,
                is_feasible=True,
                execution_time_ms=1.0,
                status="random_unknown_status",
                metrics={},
            )


class TestEvaluation(unittest.TestCase):
    """Tests for evaluate_binary_solution, repair_solution, compute_upper_bound."""

    def setUp(self) -> None:
        self.problem = KnapsackProblem(
            items=[
                Item(value=24.0, weight=12.0, id="a"),  # density = 2.0
                Item(value=13.0, weight=7.0, id="b"),   # density = 1.857
                Item(value=23.0, weight=11.0, id="c"),  # density = 2.091
                Item(value=15.0, weight=8.0, id="d"),   # density = 1.875
            ],
            capacity=20.0,
            name="eval_test",
        )

    def test_evaluate_binary_solution(self) -> None:
        val, wt, feasible = evaluate_binary_solution(self.problem, [1, 0, 0, 1])
        self.assertEqual(val, 39.0)
        self.assertEqual(wt, 20.0)
        self.assertTrue(feasible)

        val_inf, wt_inf, feasible_inf = evaluate_binary_solution(self.problem, [1, 1, 1, 1])
        self.assertEqual(val_inf, 75.0)
        self.assertEqual(wt_inf, 38.0)
        self.assertFalse(feasible_inf)

    def test_repair_solution(self) -> None:
        # Vector with all items selected (weight 38 > 20)
        # Densities: c (2.091) > a (2.0) > d (1.875) > b (1.857)
        # Under density_asc, b (lowest) dropped first -> wt: 38 - 7 = 31 > 20
        # then d (next lowest) dropped -> wt: 31 - 8 = 23 > 20
        # then a (next lowest) dropped -> wt: 23 - 12 = 11 <= 20
        # Kept: c only (index 2)
        repaired = repair_solution(self.problem, [1, 1, 1, 1], strategy="density_asc")
        val, wt, feasible = evaluate_binary_solution(self.problem, repaired)
        self.assertTrue(feasible)
        self.assertLessEqual(wt, self.problem.capacity)
        self.assertEqual(repaired, [0, 0, 1, 0])

    def test_compute_upper_bound(self) -> None:
        # Items sorted by density descending:
        # 1. c: v=23, w=11, dens=2.091
        # 2. a: v=24, w=12, dens=2.0
        # 3. d: v=15, w=8,  dens=1.875
        # 4. b: v=13, w=7,  dens=1.857
        # For capacity = 20.0, start_index = 0:
        # Takes whole c (w=11, rem=9, gain=23)
        # Takes fraction of a (rem=9, w=12 -> 9/12 * 24 = 18)
        # Total remaining gain = 23 + 18 = 41.0
        bound = compute_upper_bound(self.problem, start_index=0, remaining_capacity=20.0)
        self.assertAlmostEqual(bound, 41.0, places=5)

        # Boundary checks
        self.assertEqual(
            compute_upper_bound(self.problem, start_index=0, remaining_capacity=0.0),
            0.0,
        )
        self.assertEqual(
            compute_upper_bound(self.problem, start_index=self.problem.num_items, remaining_capacity=10.0),
            0.0,
        )
        with self.assertRaises(ValueError):
            compute_upper_bound(self.problem, start_index=-1, remaining_capacity=10.0)


class TestDatasetIO(unittest.TestCase):
    """Tests for dataset generation and JSON/CSV parsing."""

    def test_generate_dataset(self) -> None:
        prob = generate_dataset(n_items=5, capacity_ratio=0.5, seed=42)
        is_valid, msg = validate_problem(prob)
        self.assertTrue(is_valid, msg)
        self.assertEqual(prob.num_items, 5)
        self.assertGreater(prob.capacity, 0.0)

    def test_load_sample_json_and_csv(self) -> None:
        json_file = Path("assets/datasets/sample_01.json")
        csv_file = Path("assets/datasets/sample_01.csv")

        if json_file.exists():
            prob_json = load_dataset_json(str(json_file))
            self.assertEqual(prob_json.num_items, 4)
            self.assertEqual(prob_json.capacity, 20.0)

        if csv_file.exists():
            prob_csv = load_dataset_csv(str(csv_file))
            self.assertEqual(prob_csv.num_items, 4)
            self.assertEqual(prob_csv.capacity, 20.0)


if __name__ == "__main__":
    unittest.main()
