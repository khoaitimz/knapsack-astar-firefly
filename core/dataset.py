"""Dataset generation, validation, and loading utilities for 0/1 Knapsack.

Responsible member: TV1
This module provides:
- validate_problem: validates KnapsackProblem consistency and constraints.
- generate_dataset: creates synthetic knapsack instances with controlled parameters.
- load_dataset_json: loads problem instance from standardized JSON format.
- load_dataset_csv: loads problem instance from standardized CSV format.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import random

from core.knapsack import Item, KnapsackProblem


def validate_problem(problem: KnapsackProblem) -> tuple[bool, str]:
    """Validates structural and numeric integrity of a KnapsackProblem instance.

    Args:
        problem: KnapsackProblem to inspect.

    Returns:
        A tuple of (is_valid: bool, message: str).
    """
    if not isinstance(problem, KnapsackProblem):
        return False, f"Expected KnapsackProblem, got {type(problem).__name__}"

    if problem.num_items < 1:
        return False, "Problem must contain at least 1 item."

    if not math.isfinite(problem.capacity) or problem.capacity <= 0.0:
        return False, f"Capacity must be a positive finite float, got {problem.capacity}"

    for idx, item in enumerate(problem.items):
        if not isinstance(item, Item):
            return False, f"Item at index {idx} is not an Item instance."
        if not math.isfinite(item.weight) or item.weight <= 0.0:
            return False, f"Item at index {idx} has invalid weight {item.weight}"
        if not math.isfinite(item.value) or item.value < 0.0:
            return False, f"Item at index {idx} has invalid value {item.value}"

    return True, "Problem is valid."


def generate_dataset(
    n_items: int,
    capacity_ratio: float = 0.5,
    min_weight: float = 1.0,
    max_weight: float = 20.0,
    min_value: float = 1.0,
    max_value: float = 50.0,
    seed: int | None = None,
    name: str = "synthetic",
) -> KnapsackProblem:
    """Generates a synthetic 0/1 Knapsack problem with controlled characteristics.

    Args:
        n_items: Number of items to generate (must be >= 1).
        capacity_ratio: Knapsack capacity as a fraction of sum of all item weights (0.0 < ratio <= 1.0).
        min_weight: Minimum weight per item (> 0).
        max_weight: Maximum weight per item (>= min_weight).
        min_value: Minimum value per item (>= 0).
        max_value: Maximum value per item (>= min_value).
        seed: Random seed for deterministic generation.
        name: Name identifier for the generated problem.

    Returns:
        KnapsackProblem instance.

    Raises:
        ValueError: If arguments violate geometric or numeric requirements.
    """
    if n_items < 1:
        raise ValueError(f"n_items must be >= 1, got {n_items}")
    if not (0.0 < capacity_ratio <= 1.0):
        raise ValueError(f"capacity_ratio must be in (0.0, 1.0], got {capacity_ratio}")
    if min_weight <= 0.0 or max_weight < min_weight:
        raise ValueError(f"Invalid weight bounds: [{min_weight}, {max_weight}]")
    if min_value < 0.0 or max_value < min_value:
        raise ValueError(f"Invalid value bounds: [{min_value}, {max_value}]")

    rng = random.Random(seed)
    items: list[Item] = []
    total_w = 0.0

    for idx in range(n_items):
        w = round(rng.uniform(min_weight, max_weight), 2)
        v = round(rng.uniform(min_value, max_value), 2)
        items.append(Item(value=v, weight=w, id=f"item_{idx}"))
        total_w += w

    capacity = round(total_w * capacity_ratio, 2)
    # Ensure capacity is strictly positive
    if capacity <= 0.0:
        capacity = items[0].weight

    return KnapsackProblem(items=items, capacity=capacity, name=name)


def load_dataset_json(file_path: str) -> KnapsackProblem:
    """Loads a KnapsackProblem instance from a JSON file.

    Expected JSON schema:
    {
        "name": "problem_name",
        "capacity": 20.0,
        "items": [
            {"id": "item_0", "value": 24.0, "weight": 12.0},
            ...
        ]
    }

    Args:
        file_path: Absolute or relative path to the JSON file.

    Returns:
        KnapsackProblem instance.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If JSON syntax or schema is invalid.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"JSON dataset file not found: {file_path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object.")

    name = str(data.get("name", path.stem))
    if "capacity" not in data:
        raise ValueError("JSON dataset missing required 'capacity' field.")

    capacity = float(data["capacity"])
    items_raw = data.get("items")
    if not isinstance(items_raw, list) or len(items_raw) < 1:
        raise ValueError("JSON dataset must contain a non-empty 'items' list.")

    items: list[Item] = []
    for idx, raw in enumerate(items_raw):
        if not isinstance(raw, dict):
            raise ValueError(f"Item entry at index {idx} must be an object.")
        val = float(raw["value"])
        wt = float(raw["weight"])
        item_id = str(raw.get("id", f"item_{idx}"))
        items.append(Item(value=val, weight=wt, id=item_id))

    return KnapsackProblem(items=items, capacity=capacity, name=name)


def load_dataset_csv(file_path: str) -> KnapsackProblem:
    """Loads a KnapsackProblem instance from a CSV file.

    Expected CSV format:
    # capacity: 20.0
    id,value,weight
    item_0,24.0,12.0
    item_1,13.0,7.0

    If capacity comment '# capacity: <value>' is omitted, capacity defaults to
    0.5 * sum(weights).

    Args:
        file_path: Path to the CSV file.

    Returns:
        KnapsackProblem instance.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If CSV contents are malformed.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV dataset file not found: {file_path}")

    items: list[Item] = []
    capacity: float | None = None
    name = path.stem

    with path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header_parsed = False
        col_indices: dict[str, int] = {}

        for line_num, row in enumerate(reader, start=1):
            if not row:
                continue
            first_cell = row[0].strip()
            # Parse capacity comment if present
            if first_cell.startswith("#"):
                comment = ",".join(row).replace("#", "").strip()
                if "capacity" in comment.lower():
                    parts = comment.split(":")
                    if len(parts) >= 2:
                        try:
                            capacity = float(parts[1].strip())
                        except ValueError:
                            pass
                continue

            if not header_parsed:
                headers = [h.strip().lower() for h in row]
                if "value" not in headers or "weight" not in headers:
                    raise ValueError(
                        f"CSV header must contain 'value' and 'weight' columns. Got: {row}"
                    )
                col_indices["value"] = headers.index("value")
                col_indices["weight"] = headers.index("weight")
                col_indices["id"] = headers.index("id") if "id" in headers else -1
                header_parsed = True
                continue

            # Parse item row
            try:
                val = float(row[col_indices["value"]].strip())
                wt = float(row[col_indices["weight"]].strip())
                item_id = (
                    row[col_indices["id"]].strip()
                    if col_indices["id"] != -1 and len(row) > col_indices["id"]
                    else f"item_{len(items)}"
                )
            except (ValueError, IndexError) as exc:
                raise ValueError(f"Malformed row at line {line_num}: {row}") from exc

            items.append(Item(value=val, weight=wt, id=item_id))

    if not items:
        raise ValueError("No items found in CSV dataset.")

    if capacity is None:
        capacity = round(sum(it.weight for it in items) * 0.5, 2)

    return KnapsackProblem(items=items, capacity=capacity, name=name)


def save_dataset_json(problem: KnapsackProblem, file_path: str) -> None:
    """Exports a KnapsackProblem to standard JSON format."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": problem.name,
        "capacity": problem.capacity,
        "items": [
            {"id": item.id, "value": item.value, "weight": item.weight}
            for item in problem.items
        ],
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def save_dataset_csv(problem: KnapsackProblem, file_path: str) -> None:
    """Exports a KnapsackProblem to standard CSV format."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(f"# capacity: {problem.capacity}\n")
        writer = csv.writer(f)
        writer.writerow(["id", "value", "weight"])
        for item in problem.items:
            writer.writerow([item.id, item.value, item.weight])
