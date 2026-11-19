"""Firefly Algorithm Metaheuristic Solver for 0/1 Knapsack.

Responsible member: TV3

Algorithmic Design:
- Continuous Encoding:
    Each firefly represents a continuous vector Y_i in R^n bounded in [coord_min, coord_max].
- Binary Discretization:
    Continuous position is mapped to binary decision vector using sigmoid:
    sigma(y) = 1 / (1 + exp(-y))
    bit = 1 if sigma(y) >= 0.5 else 0
- Infeasibility Repair:
    Transformed vectors that violate capacity are repaired via repair_solution(..., strategy="density_asc").
- Light Intensity (Brightness):
    brightness_i = evaluate_binary_solution(problem, repaired_bits)[0] (total value).
- Movement & Attractiveness:
    Firefly i is attracted to firefly j only when brightness_j > brightness_i.
    If brightness_j <= brightness_i, no movement towards j occurs (avoiding neutral oscillations).
    Attractiveness: beta(r) = beta0 * exp(-gamma * r^2), where r = ||Y_i - Y_j||_2 / sqrt(n).
    Update: Y_i <- Y_i + beta * (Y_j - Y_i) + alpha_t * uniform_noise(-0.5, 0.5).
    Coordinates are clamped with np.clip(Y_i, coord_min, coord_max).
- Parameter Cooling:
    alpha_{t+1} = alpha_t * alpha_decay at end of each iteration.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from core.evaluation import evaluate_binary_solution, repair_solution
from core.knapsack import KnapsackProblem, SolutionResult


@dataclass
class FireflyConfig:
    """Hyperparameter configuration for Firefly Algorithm.

    Attributes:
        population_size: Number of fireflies in swarm (>= 2).
        max_iterations: Maximum search iterations (>= 1).
        alpha: Initial randomization parameter scale (>= 0.0).
        alpha_decay: Cooling multiplier per iteration (0.0 < alpha_decay <= 1.0).
        beta0: Maximum attractiveness at zero distance (>= 0.0).
        gamma: Light absorption coefficient (>= 0.0).
        coord_min: Lower bound for continuous coordinates (< coord_max).
        coord_max: Upper bound for continuous coordinates (> coord_min).
        time_limit_sec: Wall-clock timeout threshold in seconds (> 0.0).
        seed: Random seed for deterministic reproducibility (None for non-deterministic).
    """

    population_size: int = 20
    max_iterations: int = 100
    alpha: float = 0.5
    alpha_decay: float = 0.98
    beta0: float = 1.0
    gamma: float = 1.0
    coord_min: float = -6.0
    coord_max: float = 6.0
    time_limit_sec: float = 5.0
    seed: int | None = 42

    def __post_init__(self) -> None:
        if self.population_size < 2:
            raise ValueError(
                f"population_size must be >= 2, got {self.population_size}"
            )
        if self.max_iterations < 1:
            raise ValueError(
                f"max_iterations must be >= 1, got {self.max_iterations}"
            )
        if not math.isfinite(self.alpha) or self.alpha < 0.0:
            raise ValueError(f"alpha must be >= 0.0, got {self.alpha}")
        if not (0.0 < self.alpha_decay <= 1.0):
            raise ValueError(
                f"alpha_decay must be in (0.0, 1.0], got {self.alpha_decay}"
            )
        if not math.isfinite(self.beta0) or self.beta0 < 0.0:
            raise ValueError(f"beta0 must be >= 0.0, got {self.beta0}")
        if not math.isfinite(self.gamma) or self.gamma < 0.0:
            raise ValueError(f"gamma must be >= 0.0, got {self.gamma}")
        if self.coord_min >= self.coord_max:
            raise ValueError(
                f"coord_min ({self.coord_min}) must be strictly less than coord_max ({self.coord_max})"
            )
        if not math.isfinite(self.time_limit_sec) or self.time_limit_sec <= 0.0:
            raise ValueError(
                f"time_limit_sec must be positive finite float, got {self.time_limit_sec}"
            )


def solve_firefly(
    problem: KnapsackProblem,
    config: FireflyConfig | None = None,
) -> SolutionResult:
    """Solves the 0/1 Knapsack Problem using the Firefly Algorithm metaheuristic.

    Args:
        problem: KnapsackProblem instance to solve.
        config: Hyperparameter configuration. If None, default FireflyConfig() is used.

    Returns:
        SolutionResult: Standard outcome containing the best feasible solution found,
            metrics (convergence history, iterations, etc.), and status
            ("feasible", "optimal", "time_limit", "max_iter", "no_feasible_solution").

    Raises:
        NotImplementedError: Raised during the structure setup stage until TV3
            implements the complete swarm optimization loop.
    """
    if config is None:
        config = FireflyConfig()

    # Skeleton stub: enforces interface contract while waiting for TV3 implementation
    raise NotImplementedError(
        "Firefly Algorithm solver logic will be implemented by TV3 according to the theoretical specification."
    )
