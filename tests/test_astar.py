"""Correctness, feasibility and resource-limit tests for A* Search.

Responsible member: TV2
"""

from __future__ import annotations

import unittest
import itertools
import random
from unittest.mock import patch

from algorithms.astar import solve_astar
from core.evaluation import compute_upper_bound, evaluate_binary_solution
from core.knapsack import Item, KnapsackProblem, SolutionResult


class TestAStarInterface(unittest.TestCase):
    """Verifies parameter validation and interface compliance for solve_astar."""

    def setUp(self) -> None:
        self.problem = KnapsackProblem(
            items=[
                Item(value=10.0, weight=5.0, id="i1"),
                Item(value=15.0, weight=7.0, id="i2"),
            ],
            capacity=10.0,
            name="astar_test_instance",
        )

    def test_invalid_parameters_raise_value_error(self) -> None:
        for time_limit in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(time_limit=time_limit), self.assertRaises(ValueError):
                solve_astar(self.problem, time_limit_sec=time_limit)
        for node_limit in (0, -1, 1.5, float("nan"), float("inf"), True, "10", None):
            with self.subTest(node_limit=node_limit), self.assertRaises(ValueError):
                solve_astar(self.problem, max_expanded_nodes=node_limit)

    def test_full_astar_solution_contract(self) -> None:
        result = solve_astar(self.problem)
        self.assertIsInstance(result, SolutionResult)
        self.assertEqual(result.algorithm_name, "astar")
        self.assertEqual(result.status, "optimal")
        self.assertEqual(result.total_value, 15.0)
        self.assert_valid_solution(self.problem, result)

    def assert_valid_solution(self, problem: KnapsackProblem, result: SolutionResult) -> None:
        value, weight, feasible = evaluate_binary_solution(problem, result.binary_vector)
        self.assertTrue(feasible)
        self.assertTrue(result.is_feasible)
        self.assertEqual(result.total_value, value)
        self.assertEqual(result.total_weight, weight)
        self.assertEqual(result.selected_indices, [
            i for i, bit in enumerate(result.binary_vector) if bit
        ])
        self.assertGreaterEqual(result.execution_time_ms, 0.0)

    @staticmethod
    def sample_problem() -> KnapsackProblem:
        return KnapsackProblem(
            [Item(24.0, 12.0), Item(13.0, 7.0), Item(23.0, 11.0), Item(15.0, 8.0)],
            capacity=20.0,
        )

    def test_improves_greedy_and_preserves_original_indices(self) -> None:
        problem = self.sample_problem()
        original_items = problem.items
        result = solve_astar(problem)
        self.assertEqual(result.status, "optimal")
        self.assertEqual(result.selected_indices, [0, 3])
        self.assertEqual(result.binary_vector, [1, 0, 0, 1])
        self.assertEqual(result.total_value, 39.0)
        self.assertEqual(result.metrics["initial_incumbent_value"], 38.0)
        self.assertGreater(result.metrics["pruned_nodes"], 0)
        self.assertIs(problem.items, original_items)
        self.assert_valid_solution(problem, result)

    def test_matches_exhaustive_search(self) -> None:
        """Compare with an independent oracle, including zeros and tied densities."""
        rng = random.Random(42)
        for n_items in range(1, 10):
            for trial in range(8):
                problem = KnapsackProblem(
                    [Item(rng.randint(0, 25), rng.randint(1, 12)) for _ in range(n_items)],
                    capacity=rng.randint(1, 30),
                )
                expected = max(
                    value
                    for bits in itertools.product((0, 1), repeat=n_items)
                    for value, _, feasible in [evaluate_binary_solution(problem, bits)]
                    if feasible
                )
                with self.subTest(n_items=n_items, trial=trial):
                    result = solve_astar(problem)
                    self.assertEqual(result.status, "optimal")
                    self.assertEqual(result.total_value, expected)
                    self.assert_valid_solution(problem, result)

    def test_degenerate_instances(self) -> None:
        for items, capacity, expected in (
            ([Item(10.0, 2.0)], 1.0, 0.0),
            ([Item(10.0, 2.0)], 2.0, 10.0),
            ([Item(10.0, 2.0), Item(20.0, 3.0)], 5.0, 30.0),
            ([Item(0.0, 1.0), Item(0.0, 2.0)], 1.0, 0.0),
            ([Item(2.0, 2.0)] * 4, 3.0, 2.0),
            ([Item(10.0, 1.0 + 1e-13)], 1.0, 0.0),
        ):
            problem = KnapsackProblem(items, capacity)
            with self.subTest(items=items, capacity=capacity):
                result = solve_astar(problem)
                self.assertEqual(result.status, "optimal")
                self.assertEqual(result.total_value, expected)
                self.assert_valid_solution(problem, result)

    def test_small_objective_improvements_are_not_pruned(self) -> None:
        problem = self.sample_problem()
        scaled = KnapsackProblem(
            [Item(item.value * 1e-14, item.weight) for item in problem.items],
            problem.capacity,
        )
        result = solve_astar(scaled)
        self.assertEqual(result.selected_indices, [0, 3])
        self.assert_valid_solution(scaled, result)

    def test_density_sort_does_not_lose_decimal_capacity_boundary(self) -> None:
        # Input order sums to 0.6, whereas density order sums to
        # 0.6000000000000001. Feasibility must agree with core's input order.
        problem = KnapsackProblem(
            [Item(0.3, 0.3), Item(0.4, 0.2), Item(0.3, 0.1)], capacity=0.6
        )
        result = solve_astar(problem)
        self.assertEqual(result.status, "optimal")
        self.assertEqual(result.binary_vector, [1, 1, 1])
        self.assert_valid_solution(problem, result)

    def test_node_limit_returns_incumbent(self) -> None:
        problem = self.sample_problem()
        result = solve_astar(problem, max_expanded_nodes=1)
        self.assertEqual(result.status, "max_expanded")
        self.assertEqual(result.metrics["expanded_nodes"], 1)
        self.assertEqual(result.total_value, 38.0)
        self.assert_valid_solution(problem, result)

    def test_node_limit_keeps_improved_partial_selection(self) -> None:
        problem = KnapsackProblem(
            [Item(v, w) for v, w in ((5, 9), (2, 3), (27, 13), (29, 4),
                                     (5, 15), (23, 9), (18, 13))],
            capacity=18.0,
        )
        result = solve_astar(problem, max_expanded_nodes=5)
        self.assertEqual(result.status, "max_expanded")
        self.assertEqual(result.metrics["expanded_nodes"], 5)
        self.assertEqual(result.metrics["initial_incumbent_value"], 54.0)
        self.assertEqual(result.total_value, 56.0)
        self.assert_valid_solution(problem, result)

    def test_exhaustion_on_last_allowed_expansion_is_optimal(self) -> None:
        problem = KnapsackProblem([Item(10.0, 2.0)], capacity=1.0)
        result = solve_astar(problem, max_expanded_nodes=1)
        self.assertEqual(result.status, "optimal")
        self.assertEqual(result.metrics["expanded_nodes"], 1)
        self.assert_valid_solution(problem, result)

    def test_timeout_during_setup_returns_empty_feasible_solution(self) -> None:
        with patch("algorithms.astar.time.perf_counter", side_effect=[0.0] + [2.0] * 20):
            result = solve_astar(self.problem, time_limit_sec=1.0)
        self.assertEqual(result.status, "time_limit")
        self.assertEqual(result.metrics["expanded_nodes"], 0)
        self.assertEqual(result.binary_vector, [0, 0])
        self.assert_valid_solution(self.problem, result)

    def test_timeout_during_search_keeps_incumbent(self) -> None:
        clock = [0.0]
        bound_calls = 0

        def timed_bound(*args, **kwargs):
            nonlocal bound_calls
            bound_calls += 1
            if bound_calls == 3:
                clock[0] = 2.0
            return compute_upper_bound(*args, **kwargs)

        problem = self.sample_problem()
        with patch("algorithms.astar.time.perf_counter", side_effect=lambda: clock[0]), \
                patch("algorithms.astar.compute_upper_bound", side_effect=timed_bound):
            result = solve_astar(problem, time_limit_sec=1.0)
        self.assertEqual(result.status, "time_limit")
        self.assertEqual(result.metrics["expanded_nodes"], 1)
        self.assertEqual(result.total_value, 38.0)
        self.assert_valid_solution(problem, result)


if __name__ == "__main__":
    unittest.main()
