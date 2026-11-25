"""Core data models for 0/1 Knapsack Problem.

Responsible member: TV1
This module defines the foundational entities:
- Item: individual knapsack item with value, weight, and id.
- KnapsackProblem: 0/1 knapsack problem instance with items and capacity.
- SolutionResult: standard outcome contract returned by search algorithms.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import math

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


def _validate_number(value: float, name: str, *, positive: bool = False) -> None:
    """Validate numeric fields and report invalid input consistently as ValueError."""
    try:
        valid = (
            not isinstance(value, bool)
            and math.isfinite(value)
            and (value > 0.0 if positive else value >= 0.0)
        )
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        constraint = "positive" if positive else "non-negative"
        raise ValueError(f"{name} must be a {constraint} finite number, got {value!r}")


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
        _validate_number(self.weight, "Item weight", positive=True)
        _validate_number(self.value, "Item value")
        if not isinstance(self.id, str):
            raise ValueError(f"Item id must be a string, got {self.id!r}")

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
        if not isinstance(self.items, Sequence) or len(self.items) < 1:
            raise ValueError("KnapsackProblem must contain a non-empty sequence of Items.")
        _validate_number(self.capacity, "Capacity", positive=True)
        if not isinstance(self.name, str):
            raise ValueError(f"Problem name must be a string, got {self.name!r}")

        # Normalize items to tuple and auto-assign missing IDs
        normalized: list[Item] = []
        for idx, item in enumerate(self.items):
            if not isinstance(item, Item):
                raise ValueError(f"Expected Item instance at index {idx}, got {type(item).__name__}")
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

    The selected indices must be unique and match the vector's set bits; their
    order is preserved. Totals and feasibility must be computed by the solver
    against its problem, which is not stored in this result.
    """

    algorithm_name: str
    selected_indices: list[int]
    binary_vector: list[int]
    total_value: float
    total_weight: float
    is_feasible: bool
    execution_time_ms: float
    status: str
    metrics: dict[str, float | int | list[float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, str) or self.status not in VALID_SOLUTION_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}. Must be one of {sorted(VALID_SOLUTION_STATUSES)}"
            )
        _validate_number(self.total_value, "total_value")
        _validate_number(self.total_weight, "total_weight")
        _validate_number(self.execution_time_ms, "execution_time_ms")

        if not isinstance(self.algorithm_name, str):
            raise ValueError("algorithm_name must be a string.")
        if not isinstance(self.is_feasible, bool):
            raise ValueError("is_feasible must be a bool.")
        if not isinstance(self.binary_vector, list) or any(
            type(bit) is not int or bit not in (0, 1) for bit in self.binary_vector
        ):
            raise ValueError("binary_vector must be a list of integers containing only 0 or 1.")
        if not isinstance(self.selected_indices, list) or any(
            type(index) is not int or not 0 <= index < len(self.binary_vector)
            for index in self.selected_indices
        ):
            raise ValueError("selected_indices must be a list of valid 0-based integer indices.")

        selected = set(self.selected_indices)
        if len(selected) != len(self.selected_indices):
            raise ValueError("selected_indices must not contain duplicates.")
        expected = {index for index, bit in enumerate(self.binary_vector) if bit == 1}
        if selected != expected:
            raise ValueError("selected_indices must match the selected items in binary_vector.")
        if not isinstance(self.metrics, dict):
            raise ValueError("metrics must be a dictionary.")
