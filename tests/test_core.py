"""Unit tests for core models, dataset handlers, and evaluation logic.

Responsible member: TV1
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from itertools import product
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

    def test_invalid_numeric_inputs_raise_value_error(self) -> None:
        for field in ("value", "weight"):
            for value in (None, "5", True, float("nan"), float("inf"), -float("inf")):
                with self.subTest(field=field, value=value):
                    kwargs = {"value": 0.0, "weight": 1.0, field: value}
                    with self.assertRaises(ValueError):
                        Item(**kwargs)

    def test_zero_value_and_immutable_item(self) -> None:
        item = Item(value=0.0, weight=1.0)
        self.assertEqual(item.density, 0.0)
        with self.assertRaises(FrozenInstanceError):
            item.value = 1.0

    def test_non_string_id_raises(self) -> None:
        with self.assertRaises(ValueError):
            Item(value=1.0, weight=1.0, id=None)


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

    def test_input_list_is_copied_without_mutating_items(self) -> None:
        original = Item(value=10.0, weight=5.0)
        items = [original]
        problem = KnapsackProblem(items=items, capacity=5.0)
        items.clear()
        self.assertEqual(original.id, "")
        self.assertEqual(problem[0].id, "item_0")
        self.assertEqual(len(problem), 1)
        self.assertEqual(tuple(problem), problem.items)
        self.assertEqual(problem.name, "knapsack_01")

    def test_tuple_input_and_blank_id(self) -> None:
        problem = KnapsackProblem(
            items=(Item(value=1.0, weight=1.0, id="  "),), capacity=1.0
        )
        self.assertEqual(problem[0].id, "item_0")

    def test_invalid_inputs_raise_value_error(self) -> None:
        for items in (None, 1, "invalid", [None], [{"value": 1, "weight": 1}]):
            with self.subTest(items=items), self.assertRaises(ValueError):
                KnapsackProblem(items=items, capacity=1.0)
        for capacity in (None, "1", True, float("nan")):
            with self.subTest(capacity=capacity), self.assertRaises(ValueError):
                KnapsackProblem(items=[Item(value=1.0, weight=1.0)], capacity=capacity)
        with self.assertRaises(ValueError):
            KnapsackProblem(items=[Item(value=1.0, weight=1.0)], capacity=1.0, name=None)


class TestSolutionResult(unittest.TestCase):
    """Tests for SolutionResult validation."""

    def setUp(self) -> None:
        self.result = SolutionResult(
            algorithm_name="test_algo",
            selected_indices=[0, 2],
            binary_vector=[1, 0, 1],
            total_value=30.0,
            total_weight=13.0,
            is_feasible=True,
            execution_time_ms=1.5,
            status="optimal",
        )

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

    def test_all_contract_statuses_are_accepted(self) -> None:
        for status in VALID_SOLUTION_STATUSES:
            with self.subTest(status=status):
                self.assertEqual(replace(self.result, status=status).status, status)

    def test_invalid_numeric_inputs_raise_value_error(self) -> None:
        for field in ("total_value", "total_weight", "execution_time_ms"):
            for value in (-1.0, float("inf"), float("nan"), None, "1", True):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    replace(self.result, **{field: value})

    def test_invalid_solution_vectors_raise(self) -> None:
        for vector in (None, (1, 0, 1), [1, 2, 1], [1, -1, 1], [1, 0.0, 1], [True, 0, 1]):
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                replace(self.result, binary_vector=vector)
        for indices in (None, [0, 0, 2], [-1, 2], [0, 3], [0], [1, 2], [0.0, 2], [False, 2]):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                replace(self.result, selected_indices=indices)

    def test_selection_order_is_preserved(self) -> None:
        result = replace(self.result, selected_indices=[2, 0])
        self.assertEqual(result.selected_indices, [2, 0])

    def test_empty_selection_and_independent_default_metrics(self) -> None:
        result = SolutionResult(
            algorithm_name="test_algo", selected_indices=[], binary_vector=[0, 0],
            total_value=0.0, total_weight=0.0, is_feasible=True,
            execution_time_ms=0.0, status="optimal",
        )
        result.metrics["iterations"] = 1
        self.assertEqual(self.result.metrics, {})

    def test_invalid_field_types_raise_value_error(self) -> None:
        for field, value in (
            ("algorithm_name", None), ("status", []), ("is_feasible", 1), ("metrics", [])
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(self.result, **{field: value})


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
        datasets = Path(__file__).resolve().parents[1] / "assets" / "datasets"
        expected = {
            "sample_01": (4, 20.0, 39.0),
            "sample_02": (3, 50.0, 220.0),
            "sample_03": (5, 7.5, 22.0),
            "sample_04": (5, 15.0, 24.0),
            "sample_05": (3, 2.0, 0.0),
            "sample_06": (12, 35.0, 72.0),
        }
        for name, (num_items, capacity, optimum) in expected.items():
            with self.subTest(dataset=name):
                problem = load_dataset_json(str(datasets / f"{name}.json"))
                csv_problem = load_dataset_csv(str(datasets / f"{name}.csv"))
                self.assertEqual(problem, csv_problem)
                self.assertEqual(problem.num_items, num_items)
                self.assertEqual(problem.capacity, capacity)
                valid, message = validate_problem(problem)
                self.assertTrue(valid, message)

                # Exhaustive enumeration is an independent oracle for these small samples.
                solutions = (
                    evaluate_binary_solution(problem, bits)
                    for bits in product((0, 1), repeat=num_items)
                )
                best_value = max(value for value, _, feasible in solutions if feasible)
                self.assertEqual(best_value, optimum)


if __name__ == "__main__":
    unittest.main()
