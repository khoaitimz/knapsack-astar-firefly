"""Algorithms package providing 0/1 Knapsack solvers.

Solvers:
- solve_astar: Exact search using A* with fractional knapsack bounding and pruning (TV2).
- solve_firefly: Metaheuristic swarm intelligence using Firefly Algorithm (TV3).
- FireflyConfig: Configuration parameters dataclass for Firefly Algorithm.
"""

from algorithms.astar import solve_astar
from algorithms.firefly import FireflyConfig, solve_firefly

__all__ = ["solve_astar", "solve_firefly", "FireflyConfig"]
