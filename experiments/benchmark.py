"""Empirical benchmarking framework comparing A* Search and Firefly Algorithm.

Responsible member: TV4

This module executes systematic comparative experiments on problem instances,
calculates statistical summaries (mean, std, best, execution times), and exports
structured reports to CSV and JSON.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from algorithms.astar import solve_astar
from algorithms.firefly import FireflyConfig, solve_firefly
from core.knapsack import KnapsackProblem


def run_benchmark(
    problems: list[KnapsackProblem],
    firefly_config: FireflyConfig | None = None,
    fa_runs: int = 5,
    astar_time_limit_sec: float = 5.0,
    astar_max_expanded_nodes: int = 100_000,
) -> list[dict[str, float | int | str | bool]]:
    """Runs comparative benchmark between A* Search and Firefly Algorithm.

    For each problem in problems:
    - Runs solve_astar once (deterministic).
    - Runs solve_firefly for `fa_runs` repeated trials (stochastic).
    - Records metrics: total_value, total_weight, is_feasible, execution_time_ms, status.

    Args:
        problems: List of KnapsackProblem instances to benchmark.
        firefly_config: Base FireflyConfig. If None, default config is used.
        fa_runs: Number of independent runs for the Firefly Algorithm per instance (>= 1).
        astar_time_limit_sec: Time limit for A* Search.
        astar_max_expanded_nodes: Expansion limit for A* Search.

    Returns:
        List of result records (dictionaries).

    Raises:
        ValueError: If problems list is empty or fa_runs < 1.
    """
    if not problems:
        raise ValueError("Benchmark problems list cannot be empty.")
    if fa_runs < 1:
        raise ValueError(f"fa_runs must be >= 1, got {fa_runs}")

    if firefly_config is None:
        firefly_config = FireflyConfig()

    records: list[dict[str, float | int | str | bool]] = []

    for prob in problems:
        # A* execution
        try:
            astar_res = solve_astar(
                problem=prob,
                time_limit_sec=astar_time_limit_sec,
                max_expanded_nodes=astar_max_expanded_nodes,
            )
            records.append(
                {
                    "problem_name": prob.name,
                    "num_items": prob.num_items,
                    "capacity": prob.capacity,
                    "algorithm": "astar",
                    "run_id": 0,
                    "total_value": astar_res.total_value,
                    "total_weight": astar_res.total_weight,
                    "is_feasible": astar_res.is_feasible,
                    "execution_time_ms": astar_res.execution_time_ms,
                    "status": astar_res.status,
                }
            )
        except NotImplementedError:
            # During skeleton phase, mark pending
            records.append(
                {
                    "problem_name": prob.name,
                    "num_items": prob.num_items,
                    "capacity": prob.capacity,
                    "algorithm": "astar",
                    "run_id": 0,
                    "total_value": 0.0,
                    "total_weight": 0.0,
                    "is_feasible": False,
                    "execution_time_ms": 0.0,
                    "status": "pending_implementation",
                }
            )

        # Firefly repeated executions
        for run_idx in range(fa_runs):
            run_cfg = FireflyConfig(
                population_size=firefly_config.population_size,
                max_iterations=firefly_config.max_iterations,
                alpha=firefly_config.alpha,
                alpha_decay=firefly_config.alpha_decay,
                beta0=firefly_config.beta0,
                gamma=firefly_config.gamma,
                coord_min=firefly_config.coord_min,
                coord_max=firefly_config.coord_max,
                time_limit_sec=firefly_config.time_limit_sec,
                seed=(firefly_config.seed + run_idx) if firefly_config.seed is not None else None,
            )
            try:
                fa_res = solve_firefly(problem=prob, config=run_cfg)
                records.append(
                    {
                        "problem_name": prob.name,
                        "num_items": prob.num_items,
                        "capacity": prob.capacity,
                        "algorithm": "firefly",
                        "run_id": run_idx,
                        "total_value": fa_res.total_value,
                        "total_weight": fa_res.total_weight,
                        "is_feasible": fa_res.is_feasible,
                        "execution_time_ms": fa_res.execution_time_ms,
                        "status": fa_res.status,
                    }
                )
            except NotImplementedError:
                records.append(
                    {
                        "problem_name": prob.name,
                        "num_items": prob.num_items,
                        "capacity": prob.capacity,
                        "algorithm": "firefly",
                        "run_id": run_idx,
                        "total_value": 0.0,
                        "total_weight": 0.0,
                        "is_feasible": False,
                        "execution_time_ms": 0.0,
                        "status": "pending_implementation",
                    }
                )

    return records


def export_benchmark_results(
    records: list[dict[str, float | int | str | bool]],
    output_dir: str = "experiments/results",
) -> dict[str, str]:
    """Exports benchmark records to CSV and JSON files in output_dir.

    Args:
        records: List of benchmark result dictionaries.
        output_dir: Destination directory path.

    Returns:
        Dictionary with keys 'csv_path' and 'json_path' mapping to saved file paths.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    csv_path = out_path / "benchmark_records.csv"
    json_path = out_path / "benchmark_records.json"

    # Export CSV
    if records:
        fieldnames = list(records[0].keys())
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    # Export JSON
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    return {
        "csv_path": str(csv_path),
        "json_path": str(json_path),
    }
