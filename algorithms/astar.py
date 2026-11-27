"""A* Search Algorithm with Branch-and-Bound Pruning for 0/1 Knapsack.

Responsible member: TV2

Mathematical Formulation:
- State Representation at decision level (0 <= level <= n):
    State: (level, current_weight, current_value, chosen_mask)
- Decision Tree Actions:
    1. Take item at level (action = 1): valid if current_weight + item.weight <= capacity.
    2. Skip item at level (action = 0): always valid.
- Edge Costs and Cost Function g(n):
    Formulated as minimizing forfeited/missed value:
    Edge cost for taking item k: 0.0
    Edge cost for skipping item k: v_k
    g(n) = sum_{k=0}^{level-1} v_k * (1 - x_k) = sum_{k=0}^{level-1} v_k - current_value(n) >= 0.
- Heuristic Function h(n) and Evaluation Function f(n):
    Let rem_gain = compute_upper_bound(problem, level, rem_cap, sorted_indices)
    h(n) = max(0.0, V_rem(n) - rem_gain), where V_rem(n) = sum_{k=level}^{n-1} v_k
    f(n) = g(n) + h(n) = V_all - max_possible_value(n)
    h(n) is admissible because fractional relaxation bounds all discrete binary completions.
- Pruning:
    Branch-and-Bound pruning cuts off nodes where:
    current_value(n) + rem_gain <= best_feasible_value.
"""

from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass

from core.evaluation import compute_upper_bound, evaluate_binary_solution
from core.knapsack import KnapsackProblem, SolutionResult


@dataclass(frozen=True, slots=True)
class _AStarState:
    """A node in the fixed-order 0/1 knapsack decision tree.

    ``level`` is the number of items in ``sorted_indices`` already decided and
    ``chosen_mask`` stores the selected positions in the original problem.  The
    mask compactly records the path while keeping states immutable for the
    priority queue.
    """

    level: int
    current_weight: float
    current_value: float
    chosen_mask: int
    g_cost: float
    h_cost: float
    upper_bound: float

    @property
    def f_cost(self) -> float:
        return self.g_cost + self.h_cost


def solve_astar(
    problem: KnapsackProblem,
    time_limit_sec: float = 5.0,
    max_expanded_nodes: int = 100_000,
) -> SolutionResult:
    """Solves the 0/1 Knapsack Problem using A* Search with upper-bound pruning.

    Args:
        problem: KnapsackProblem instance to solve.
        time_limit_sec: Maximum wall-clock time limit in seconds (strictly positive).
        max_expanded_nodes: Maximum allowable node expansions before stopping.

    Returns:
        SolutionResult: Standard outcome containing chosen items, metrics, and status
            ("optimal", "time_limit", or "max_expanded"). The empty selection is
            feasible even when no item fits. Limits are checked cooperatively
            during setup and between node expansions; setup counts toward time.

    Raises:
        ValueError: If the resource limits are invalid.
    """
    if not math.isfinite(time_limit_sec) or time_limit_sec <= 0.0:
        raise ValueError(
            f"time_limit_sec must be a positive finite float, got {time_limit_sec!r}"
        )
    if (
        isinstance(max_expanded_nodes, bool)
        or not isinstance(max_expanded_nodes, int)
        or max_expanded_nodes < 1
    ):
        raise ValueError(
            f"max_expanded_nodes must be an integer >= 1, got {max_expanded_nodes!r}"
        )

    started = time.perf_counter()
    n_items = problem.num_items
    capacity = problem.capacity
    # Different summation orders may differ by a few ulps. Use conservative
    # search capacity so sorting cannot discard a feasible boundary solution;
    # consider_solution still enforces core's strict, original-order capacity.
    search_capacity = capacity + n_items * math.ulp(capacity)

    def elapsed() -> float:
        return time.perf_counter() - started

    # A* and the fractional bound use the same order.  The order is only an
    # internal search detail, so the returned vector remains in input order.
    sorted_indices = tuple(
        sorted(range(n_items), key=lambda index: problem[index].density, reverse=True)
    )
    remaining_values = [0.0] * (n_items + 1)
    for level in range(n_items - 1, -1, -1):
        remaining_values[level] = (
            remaining_values[level + 1] + problem[sorted_indices[level]].value
        )

    # Obtain an inexpensive feasible incumbent before expanding the tree.  It
    # substantially increases the amount of branch-and-bound pruning while the
    # empty solution guarantees feasibility for every valid problem instance.
    greedy_mask = 0
    greedy_weight = 0.0
    greedy_value = 0.0
    for item_index in sorted_indices:
        if elapsed() >= time_limit_sec:
            break
        item = problem[item_index]
        if item.value > 0.0 and greedy_weight + item.weight <= search_capacity:
            greedy_weight += item.weight
            greedy_value += item.value
            greedy_mask |= 1 << item_index

    best_value = 0.0
    best_mask = 0

    def consider_solution(mask: int, value: float) -> None:
        nonlocal best_mask, best_value
        if value > best_value:
            # Evaluate in input order, matching core's floating-point sums and
            # strict feasibility check, before accepting an incumbent.
            bits = [int(bool(mask & (1 << index))) for index in range(n_items)]
            candidate_value, _, feasible = evaluate_binary_solution(problem, bits)
            if feasible and candidate_value > best_value:
                best_value = candidate_value
                best_mask = mask

    consider_solution(greedy_mask, greedy_value)
    initial_incumbent = best_value

    def make_result(
        status: str, *, expanded: int, generated: int, pruned: int, max_frontier: int
    ) -> SolutionResult:
        binary_vector = [
            1 if (best_mask & (1 << index)) else 0 for index in range(n_items)
        ]
        selected_indices = [index for index, bit in enumerate(binary_vector) if bit]
        total_value, total_weight, feasible = evaluate_binary_solution(
            problem, binary_vector
        )
        return SolutionResult(
            algorithm_name="astar",
            selected_indices=selected_indices,
            binary_vector=binary_vector,
            total_value=float(total_value),
            total_weight=float(total_weight),
            is_feasible=feasible,
            execution_time_ms=max(0.0, elapsed() * 1000.0),
            status=status,
            metrics={
                "expanded_nodes": expanded,
                "generated_nodes": generated,
                "pruned_nodes": pruned,
                "max_frontier_size": max_frontier,
                "initial_incumbent_value": float(initial_incumbent),
            },
        )

    if elapsed() >= time_limit_sec:
        return make_result(
            "time_limit", expanded=0, generated=0, pruned=0, max_frontier=0
        )

    # The root's g cost is zero: no item has been skipped.  For a node at level
    # k, g is the total value forfeited by skip edges among the first k items.
    root_bound = compute_upper_bound(
        problem, 0, search_capacity, sorted_indices=sorted_indices
    )
    root = _AStarState(
        level=0,
        current_weight=0.0,
        current_value=0.0,
        chosen_mask=0,
        g_cost=0.0,
        h_cost=max(0.0, remaining_values[0] - root_bound),
        upper_bound=root_bound,
    )

    # Heap key is f(n)=V_all-upper_bound(n), so the node with the largest
    # attainable value is expanded first.  A monotonically increasing counter
    # avoids comparing state objects when keys tie.
    queue: list[tuple[float, int, _AStarState]] = []
    counter = 0
    heapq.heappush(queue, (root.f_cost, counter, root))
    generated_nodes = 1
    expanded_nodes = 0
    pruned_nodes = 0
    max_frontier = 1
    status = "optimal"

    while queue:
        if elapsed() >= time_limit_sec:
            status = "time_limit"
            break
        _, _, state = heapq.heappop(queue)
        # An incumbent can improve after this node was enqueued.  Recheck its
        # bound when popped to avoid expanding stale dominated work.
        if state.upper_bound <= best_value:
            pruned_nodes += 1
            continue
        if expanded_nodes >= max_expanded_nodes:
            status = "max_expanded"
            break

        expanded_nodes += 1
        item_index = sorted_indices[state.level]
        item = problem[item_index]
        next_level = state.level + 1

        def enqueue_child(
            *, weight: float, value: float, mask: int, edge_cost: float
        ) -> None:
            nonlocal counter, generated_nodes, pruned_nodes, max_frontier
            generated_nodes += 1
            # Undecided items may all be skipped, so every partial node is a
            # feasible complete selection. Save it before pruning or stopping.
            consider_solution(mask, value)
            remaining_capacity = search_capacity - weight
            remaining_gain = compute_upper_bound(
                problem,
                next_level,
                remaining_capacity,
                sorted_indices=sorted_indices,
            )
            child_upper = value + remaining_gain
            # The branch cannot improve the incumbent.  Equality is safe to
            # prune because the solver only needs one optimal solution.
            if next_level == n_items or child_upper <= best_value:
                pruned_nodes += 1
                return

            child = _AStarState(
                level=next_level,
                current_weight=weight,
                current_value=value,
                chosen_mask=mask,
                g_cost=state.g_cost + edge_cost,
                h_cost=max(0.0, remaining_values[next_level] - remaining_gain),
                upper_bound=child_upper,
            )
            counter += 1
            heapq.heappush(queue, (child.f_cost, counter, child))
            max_frontier = max(max_frontier, len(queue))

        # Taking an item has zero forfeiture edge cost. Only complete feasible
        # selections validated in input order can become the incumbent.
        if state.current_weight + item.weight <= search_capacity:
            enqueue_child(
                weight=state.current_weight + item.weight,
                value=state.current_value + item.value,
                mask=state.chosen_mask | (1 << item_index),
                edge_cost=0.0,
            )

        # Skipping an item incurs its value as the forfeiture edge cost.
        enqueue_child(
            weight=state.current_weight,
            value=state.current_value,
            mask=state.chosen_mask,
            edge_cost=item.value,
        )

    return make_result(
        status,
        expanded=expanded_nodes,
        generated=generated_nodes,
        pruned=pruned_nodes,
        max_frontier=max_frontier,
    )
