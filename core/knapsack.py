"""Core data models for 0/1 Knapsack Problem.

Responsible member: TV1
This module defines the foundational entities:
- Item: individual knapsack item with value, weight, and id.
- KnapsackProblem: 0/1 knapsack problem instance with items and capacity.
- SolutionResult: standard outcome contract returned by search algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Sequence

# Valid statuses defined in INTERFACE_CONTRACT.md
VALID_SOLUTION_STATUSES = frozenset(
    {
        "optimal",
        "feasible",
        "time_limit",
        "max_iter",
        "max_expanded",
        "no_feasible_solution",
    }
)


@dataclass(frozen=True)
class Item:
    """Represents a discrete item for the 0/1 knapsack problem.

    Attributes:
        value: Non-negative finite float representing the item's benefit/profit.
        weight: Strictly positive finite float representing the item's weight.
        id: Optional unique identifier string. If empty, will be auto-assigned
            when added to a KnapsackProblem.
    """

    value: float
    weight: float
    id: str = ""

    def __post_init__(self) -> None:
        if not math.isfinite(self.weight) or self.weight <= 0.0:
            raise ValueError(
                f"Item weight must be a positive finite float, got {self.weight!r}"
            )
        if not math.isfinite(self.value) or self.value < 0.0:
            raise ValueError(
                f"Item value must be a non-negative finite float, got {self.value!r}"
            )

    @property
    def density(self) -> float:
        """Returns the efficiency ratio value / weight."""
        return self.value / self.weight


@dataclass
class KnapsackProblem:
    """Represents an instance of the 0/1 Knapsack Problem.

    Attributes:
        items: Sequence of items available for selection.
        capacity: Strictly positive finite float representing maximum capacity.
        name: Identifier name for the instance.
    """

    items: Sequence[Item]
    capacity: float
    name: str = "knapsack_01"
    _items_tuple: tuple[Item, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.items or len(self.items) < 1:
            raise ValueError("KnapsackProblem must contain at least 1 item.")
        if not math.isfinite(self.capacity) or self.capacity <= 0.0:
            raise ValueError(
                f"Capacity must be a positive finite float, got {self.capacity!r}"
            )

        # Normalize items to tuple and auto-assign missing IDs
        normalized: list[Item] = []
        for idx, item in enumerate(self.items):
            if not isinstance(item, Item):
                raise TypeError(f"Expected Item instance at index {idx}, got {type(item)}")
            if item.id.strip() == "":
                normalized.append(Item(value=item.value, weight=item.weight, id=f"item_{idx}"))
            else:
                normalized.append(item)
        self._items_tuple = tuple(normalized)
        self.items = self._items_tuple

    @property
    def num_items(self) -> int:
        """Total number of items in the problem instance."""
        return len(self._items_tuple)

    @property
    def total_value(self) -> float:
        """Sum of values of all items."""
        return sum(it.value for it in self._items_tuple)

    @property
    def total_weight(self) -> float:
        """Sum of weights of all items."""
        return sum(it.weight for it in self._items_tuple)

    def __getitem__(self, index: int) -> Item:
        return self._items_tuple[index]

    def __len__(self) -> int:
        return len(self._items_tuple)


@dataclass
class SolutionResult:
    """Standardized output structure returned by all knapsack solving algorithms.

    Attributes:
        algorithm_name: Identifier name of algorithm ("astar", "firefly", etc.).
        selected_indices: 0-based indices of chosen items in the problem.
        binary_vector: 0/1 binary decision vector of length equal to problem.num_items.
        total_value: Total accumulated value of chosen items.
        total_weight: Total accumulated weight of chosen items.
        is_feasible: True if total_weight <= problem.capacity, False otherwise.
        execution_time_ms: Wall-clock execution time in milliseconds.
        status: Convergence status, must be one of:
            {"optimal", "feasible", "time_limit", "max_iter", "max_expanded", "no_feasible_solution"}
        metrics: Dictionary of algorithm-specific instrumentation metrics
            (e.g., expanded_nodes, generated_nodes, convergence_history, iterations).
    """

    algorithm_name: str
    selected_indices: list[int]
    binary_vector: list[int]
    total_value: float
    total_weight: float
    is_feasible: bool
    execution_time_ms: float
    status: str
    metrics: dict[str, float | int | list[float]]

    def __post_init__(self) -> None:
        if self.status not in VALID_SOLUTION_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}. Must be one of {sorted(VALID_SOLUTION_STATUSES)}"
            )
        if not math.isfinite(self.total_value) or self.total_value < 0.0:
            raise ValueError(f"total_value must be non-negative finite float, got {self.total_value!r}")
        if not math.isfinite(self.total_weight) or self.total_weight < 0.0:
            raise ValueError(f"total_weight must be non-negative finite float, got {self.total_weight!r}")
        if not math.isfinite(self.execution_time_ms) or self.execution_time_ms < 0.0:
            raise ValueError(
                f"execution_time_ms must be non-negative finite float, got {self.execution_time_ms!r}"
            )
