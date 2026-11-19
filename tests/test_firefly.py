"""Tests for Firefly Algorithm interface and configuration compliance.

Responsible member: TV3
"""

from __future__ import annotations

import unittest

from algorithms.firefly import FireflyConfig, solve_firefly
from core.knapsack import Item, KnapsackProblem, SolutionResult


class TestFireflyConfig(unittest.TestCase):
    """Verifies boundary checks and parameter validation in FireflyConfig."""

    def test_default_config(self) -> None:
        cfg = FireflyConfig()
        self.assertEqual(cfg.population_size, 20)
        self.assertEqual(cfg.max_iterations, 100)
        self.assertEqual(cfg.alpha, 0.5)
        self.assertEqual(cfg.alpha_decay, 0.98)
        self.assertEqual(cfg.beta0, 1.0)
        self.assertEqual(cfg.gamma, 1.0)
        self.assertEqual(cfg.coord_min, -6.0)
        self.assertEqual(cfg.coord_max, 6.0)
        self.assertEqual(cfg.time_limit_sec, 5.0)
        self.assertEqual(cfg.seed, 42)

    def test_invalid_parameters_raise(self) -> None:
        with self.assertRaises(ValueError):
            FireflyConfig(population_size=1)
        with self.assertRaises(ValueError):
            FireflyConfig(max_iterations=0)
        with self.assertRaises(ValueError):
            FireflyConfig(alpha=-0.1)
        with self.assertRaises(ValueError):
            FireflyConfig(alpha_decay=0.0)
        with self.assertRaises(ValueError):
            FireflyConfig(alpha_decay=1.1)
        with self.assertRaises(ValueError):
            FireflyConfig(coord_min=5.0, coord_max=2.0)
        with self.assertRaises(ValueError):
            FireflyConfig(time_limit_sec=0.0)


class TestFireflyInterface(unittest.TestCase):
    """Verifies solve_firefly signature and contract compliance."""

    def setUp(self) -> None:
        self.problem = KnapsackProblem(
            items=[
                Item(value=10.0, weight=5.0, id="i1"),
                Item(value=15.0, weight=7.0, id="i2"),
            ],
            capacity=10.0,
            name="firefly_test_instance",
        )

    def test_signature_and_stub_raises_not_implemented(self) -> None:
        """Confirms solve_firefly raises NotImplementedError during structure phase."""
        with self.assertRaises(NotImplementedError):
            solve_firefly(self.problem, FireflyConfig())

    @unittest.skip("Firefly Algorithm metaheuristic implementation pending TV3.")
    def test_full_firefly_solution_contract(self) -> None:
        """Will verify that solve_firefly returns a valid SolutionResult once implemented by TV3."""
        result = solve_firefly(self.problem)
        self.assertIsInstance(result, SolutionResult)
        self.assertEqual(result.algorithm_name, "firefly")
        self.assertIn(result.status, {"feasible", "optimal", "time_limit", "max_iter"})


if __name__ == "__main__":
    unittest.main()
