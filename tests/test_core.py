"""Unit tests for core models, dataset handlers, and evaluation logic.

Responsible member: TV1
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from itertools import product
import json
from pathlib import Path
import random
import tempfile
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

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def write_dataset(self, filename: str, content: str) -> str:
        path = self.directory / filename
        path.write_text(content, encoding="utf-8-sig")
        return str(path)

    def test_generate_dataset(self) -> None:
        prob = generate_dataset(n_items=5, capacity_ratio=0.5, seed=42)
        is_valid, msg = validate_problem(prob)
        self.assertTrue(is_valid, msg)
        self.assertEqual(prob.num_items, 5)
        self.assertGreater(prob.capacity, 0.0)

    def test_validate_problem_rejects_wrong_type(self) -> None:
        for problem in (None, {}, [], "problem"):
            with self.subTest(problem=problem):
                valid, message = validate_problem(problem)
                self.assertFalse(valid)
                self.assertTrue(message)

    def test_validate_problem_handles_mutated_fields(self) -> None:
        for field, value in (
            ("capacity", None), ("capacity", "5"), ("capacity", True),
            ("capacity", float("nan")), ("capacity", float("inf")),
            ("capacity", 0.0), ("capacity", -1.0), ("name", None),
            ("items", None), ("items", []), ("items", [None]),
            ("items", [Item(value=2.0, weight=1.0)]),
        ):
            with self.subTest(field=field, value=value):
                problem = KnapsackProblem([Item(value=1.0, weight=1.0)], capacity=1.0)
                setattr(problem, field, value)
                valid, message = validate_problem(problem)
                self.assertFalse(valid)
                self.assertTrue(message)

    def test_generate_dataset_is_reproducible_without_changing_global_rng(self) -> None:
        state = random.getstate()
        first = generate_dataset(10, seed=42, name="repeatable")
        second = generate_dataset(10, seed=42, name="repeatable")
        self.assertEqual(first, second)
        self.assertEqual(random.getstate(), state)
        self.assertNotEqual(first.items, generate_dataset(10, seed=43).items)
        self.assertEqual([item.id for item in first.items], [f"item_{i}" for i in range(10)])
        self.assertEqual(first.capacity, first.total_weight * 0.5)

    def test_generate_dataset_rejects_invalid_arguments(self) -> None:
        invalid = [
            {"n_items": value} for value in (0, -1, 1.5, True, None, "2")
        ]
        invalid.extend(
            {field: value}
            for field in ("capacity_ratio", "min_weight", "max_weight", "min_value", "max_value")
            for value in (None, "1", True, float("nan"), float("inf"), -float("inf"))
        )
        invalid.extend([
            {"capacity_ratio": 0.0}, {"capacity_ratio": 1.01},
            {"min_weight": 0.0}, {"min_weight": -1.0},
            {"min_weight": 3.0, "max_weight": 2.0},
            {"min_value": -1.0}, {"min_value": 3.0, "max_value": 2.0},
            {"seed": True}, {"seed": 1.5}, {"seed": "42"}, {"name": None},
        ])
        for overrides in invalid:
            kwargs = {"n_items": 2, **overrides}
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                generate_dataset(**kwargs)

    def test_generate_dataset_preserves_small_bounds_and_capacity_ratio(self) -> None:
        problem = generate_dataset(
            2, capacity_ratio=0.25, min_weight=0.003, max_weight=0.003,
            min_value=0.0, max_value=0.0, seed=0,
        )
        self.assertEqual([item.weight for item in problem.items], [0.003, 0.003])
        self.assertEqual(problem.total_value, 0.0)
        self.assertEqual(problem.capacity, 0.0015)
        self.assertTrue(validate_problem(problem)[0])

    def test_generate_dataset_stays_within_narrow_bounds(self) -> None:
        problem = generate_dataset(
            20, capacity_ratio=1.0, min_weight=1.001, max_weight=1.002,
            min_value=0.001, max_value=0.002, seed=0,
        )
        for item in problem.items:
            self.assertTrue(1.001 <= item.weight <= 1.002)
            self.assertTrue(0.001 <= item.value <= 0.002)
        self.assertEqual(problem.capacity, problem.total_weight)

    def test_generate_dataset_rejects_unrepresentable_capacity(self) -> None:
        with self.assertRaises(ValueError):
            generate_dataset(2, min_weight=1e308, max_weight=1e308)
        with self.assertRaises(ValueError):
            generate_dataset(1, min_weight=1e-300, max_weight=1e-300, capacity_ratio=1e-300)

    def test_loaders_report_missing_files(self) -> None:
        for loader, extension in ((load_dataset_json, "json"), (load_dataset_csv, "csv")):
            with self.subTest(extension=extension), self.assertRaises(FileNotFoundError):
                loader(str(self.directory / f"missing.{extension}"))

    def test_json_defaults_numeric_strings_and_utf8_bom(self) -> None:
        payload = {
            "capacity": "2.5",
            "items": [
                {"value": "4.5", "weight": "1.5"},
                {"id": "vật_phẩm", "value": 0, "weight": 1},
            ],
        }
        path = self.write_dataset("unicode.json", json.dumps(payload, ensure_ascii=False))
        problem = load_dataset_json(path)
        self.assertEqual(problem.name, "unicode")
        self.assertEqual(problem.capacity, 2.5)
        self.assertEqual(problem[0], Item(value=4.5, weight=1.5, id="item_0"))
        self.assertEqual(problem[1].id, "vật_phẩm")

    def test_json_rejects_invalid_schema_and_numbers(self) -> None:
        item = {"value": 1, "weight": 1}
        invalid = [
            [], None, {}, {"items": [item]}, {"capacity": 1},
            {"capacity": 1, "items": []}, {"capacity": 1, "items": {}},
            {"capacity": 1, "items": [None]},
            {"capacity": 1, "items": [{"value": 1}]},
            {"capacity": 1, "items": [{"weight": 1}]},
            {"capacity": 1, "items": [item], "name": None},
            {"capacity": 1, "items": [{**item, "id": None}]},
        ]
        invalid.extend(
            {"capacity": value, "items": [item]}
            for value in (None, True, 0, -1, "bad", float("nan"), float("inf"), 10**400)
        )
        invalid.extend(
            {"capacity": 1, "items": [{**item, field: value}]}
            for field in ("value", "weight")
            for value in (None, True, -1, [], "bad", float("nan"), float("inf"))
        )
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                load_dataset_json(self.write_dataset("invalid.json", json.dumps(payload)))
        with self.assertRaises(ValueError):
            load_dataset_json(self.write_dataset("invalid.json", '{"capacity":'))

    def test_csv_defaults_capacity_and_item_ids_without_rounding_to_zero(self) -> None:
        path = self.write_dataset("tiny.csv", "value,weight\n0,0.003\n2,0.001\n")
        problem = load_dataset_csv(path)
        self.assertEqual(problem.name, "tiny")
        self.assertEqual(problem.capacity, 0.002)
        self.assertEqual([item.id for item in problem.items], ["item_0", "item_1"])

    def test_csv_handles_bom_comments_reordered_columns_and_quoted_ids(self) -> None:
        path = self.write_dataset(
            "flexible.csv",
            '\n  \n# description: example\n# CAPACITY : 2.5\n WEIGHT , ID , VALUE \n'
            '1.5,"vật,phẩm",4.5\n1,,0\n',
        )
        problem = load_dataset_csv(path)
        self.assertEqual(problem.capacity, 2.5)
        self.assertEqual(problem.items, (
            Item(value=4.5, weight=1.5, id="vật,phẩm"),
            Item(value=0.0, weight=1.0, id="item_1"),
        ))

    def test_csv_rejects_invalid_rows_headers_and_capacity(self) -> None:
        invalid = [
            "", "# just a comment\n", "id,value,weight\n",
            "id,value\na,1\n", "value,weight,weight\n1,1,1\n",
            "id,value,weight\na,1\n", "value,weight\n1,1,extra\n",
            'id,value,weight\n"unterminated,1,1\n',
            "value,weight\n1,0\n", "value,weight\n-1,1\n",
            "value,weight\nNaN,1\n", "value,weight\n1,inf\n",
            "value,weight\nbad,1\n", "value,weight\n,1\n",
            "# capacity\nvalue,weight\n1,1\n",
            "# capacity: 1\n# capacity: 2\nvalue,weight\n1,1\n",
        ]
        invalid.extend(
            f"# capacity: {capacity}\nvalue,weight\n1,1\n"
            for capacity in ("", "bad", "0", "-1", "NaN", "inf", "True")
        )
        for content in invalid:
            with self.subTest(content=content), self.assertRaises(ValueError):
                load_dataset_csv(self.write_dataset("invalid.csv", content))

    def test_loaders_reject_invalid_utf8(self) -> None:
        for loader, filename, content in (
            (load_dataset_json, "invalid.json", b'{"capacity":1,"items":[{"id":"\xff","value":1,"weight":1}]}'),
            (load_dataset_csv, "invalid.csv", b"id,value,weight\n\xff,1,1\n"),
        ):
            path = self.directory / filename
            path.write_bytes(content)
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                loader(str(path))

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
