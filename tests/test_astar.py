"""Tests for A* Search algorithm interface and contract compliance.

Responsible member: TV2
"""

from __future__ import annotations

import unittest

from algorithms.astar import solve_astar
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
        with self.assertRaises(ValueError):
            solve_astar(self.problem, time_limit_sec=0.0)

        with self.assertRaises(ValueError):
            solve_astar(self.problem, time_limit_sec=-1.0)

        with self.assertRaises(ValueError):
            solve_astar(self.problem, max_expanded_nodes=0)

    def test_signature_and_stub_raises_not_implemented(self) -> None:
        """Confirms solve_astar raises NotImplementedError during structure phase."""
        with self.assertRaises(NotImplementedError):
            solve_astar(self.problem, time_limit_sec=5.0, max_expanded_nodes=100)

    @unittest.skip("Full A* search tree traversal implementation pending TV2.")
    def test_full_astar_solution_contract(self) -> None:
        """Will verify that solve_astar returns a valid SolutionResult once implemented by TV2."""
        result = solve_astar(self.problem)
        self.assertIsInstance(result, SolutionResult)
        self.assertEqual(result.algorithm_name, "astar")
        self.assertIn(result.status, {"optimal", "feasible", "time_limit", "max_expanded"})


if __name__ == "__main__":
    unittest.main()
