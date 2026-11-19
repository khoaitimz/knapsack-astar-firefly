"""Evaluation, repair, and bounding functions for 0/1 Knapsack solutions.

Responsible member: TV1
This module provides:
- evaluate_binary_solution: calculates total value, weight, and feasibility.
- repair_solution: repairs infeasible binary solutions (used by Firefly Algorithm).
- compute_upper_bound: calculates fractional relaxation upper bound gain (used by A*).
"""

from __future__ import annotations

import math
from typing import Sequence

from core.knapsack import KnapsackProblem


def evaluate_binary_solution(
    problem: KnapsackProblem,
    binary_vector: list[int] | tuple[int, ...],
) -> tuple[float, float, bool]:
    """Evaluates a binary selection vector against a knapsack instance.

    Args:
        problem: KnapsackProblem instance.
        binary_vector: Sequence of 0s and 1s corresponding to item choices.

    Returns:
        A tuple of (total_value, total_weight, is_feasible).

    Raises:
        ValueError: If vector length does not match problem item count or contains
            elements other than 0 and 1.
    """
    if len(binary_vector) != problem.num_items:
        raise ValueError(
            f"Binary vector length ({len(binary_vector)}) must match problem items ({problem.num_items})"
        )

    total_value = 0.0
    total_weight = 0.0

    for bit, item in zip(binary_vector, problem.items):
        if bit == 1:
            total_value += item.value
            total_weight += item.weight
        elif bit != 0:
            raise ValueError(f"Binary vector elements must be 0 or 1, encountered {bit!r}")

    is_feasible = total_weight <= problem.capacity
    return total_value, total_weight, is_feasible


def repair_solution(
    problem: KnapsackProblem,
    binary_vector: list[int] | tuple[int, ...],
    strategy: str = "density_asc",
) -> list[int]:
    """Repairs an infeasible binary knapsack vector by dropping items until feasible.

    Args:
        problem: KnapsackProblem instance.
        binary_vector: Binary vector that may exceed knapsack capacity.
        strategy: Repair heuristic order. Currently supports 'density_asc'
            (drops items with the lowest value/weight ratio first).

    Returns:
        A feasible binary vector (list[int]).

    Raises:
        ValueError: If vector length is invalid or an unsupported strategy is passed.
    """
    if strategy != "density_asc":
        raise ValueError(
            f"Unsupported repair strategy: {strategy!r}. Supported: ['density_asc']"
        )

    total_val, total_wt, is_feasible = evaluate_binary_solution(problem, binary_vector)
    if is_feasible:
        return list(binary_vector)

    repaired = list(binary_vector)
    current_weight = total_wt

    # Find active indices and sort by density ascending (lowest value/weight first)
    # Tie-break with higher weight first to shed capacity rapidly
    active_indices = [idx for idx, bit in enumerate(repaired) if bit == 1]
    active_indices.sort(
        key=lambda idx: (problem[idx].density, -problem[idx].weight)
    )

    for idx in active_indices:
        if current_weight <= problem.capacity:
            break
        repaired[idx] = 0
        current_weight -= problem[idx].weight

    return repaired


def compute_upper_bound(
    problem: KnapsackProblem,
    start_index: int,
    remaining_capacity: float,
    sorted_indices: tuple[int, ...] | None = None,
) -> float:
    """Computes the continuous fractional knapsack upper bound gain for remaining items.

    This function strictly computes the remaining fractional gain from `start_index`
    onward. It does NOT include current_value of previously selected items.

    Args:
        problem: KnapsackProblem instance.
        start_index: Position in sorted_indices from which to consider remaining items.
        remaining_capacity: Remaining available knapsack capacity.
        sorted_indices: Tuple of item indices sorted in descending order of density.
            If None, will be computed automatically.

    Returns:
        remaining_fractional_gain: Maximum potential additional value obtainable
            from remaining items.

    Raises:
        ValueError: If start_index < 0 or start_index > problem.num_items.
    """
    if start_index < 0 or start_index > problem.num_items:
        raise ValueError(
            f"start_index must be between 0 and {problem.num_items}, got {start_index}"
        )

    if remaining_capacity <= 0.0 or start_index == problem.num_items:
        return 0.0

    if sorted_indices is None:
        sorted_indices = tuple(
            sorted(
                range(problem.num_items),
                key=lambda idx: problem[idx].density,
                reverse=True,
            )
        )

    remaining_gain = 0.0
    rem_cap = remaining_capacity

    for k in range(start_index, len(sorted_indices)):
        item_idx = sorted_indices[k]
        item = problem[item_idx]

        if item.weight <= rem_cap:
            rem_cap -= item.weight
            remaining_gain += item.value
            if rem_cap <= 1e-12:
                break
        else:
            # Fractional take of the critical item
            remaining_gain += (rem_cap / item.weight) * item.value
            break

    return remaining_gain
