"""Dataset generation, validation, and loading utilities for 0/1 Knapsack.

Responsible member: TV1
This module provides:
- validate_problem: validates KnapsackProblem consistency and constraints.
- generate_dataset: creates synthetic knapsack instances with controlled parameters.
- load_dataset_json: loads problem instance from standardized JSON format.
- load_dataset_csv: loads problem instance from standardized CSV format.
"""

from __future__ import annotations

from collections.abc import Sequence
import csv
import json
import math
from pathlib import Path
import random

from core.knapsack import Item, KnapsackProblem


def _is_finite_number(value: object) -> bool:
    """Check numeric input without accepting booleans or raising type errors."""
    try:
        return not isinstance(value, bool) and math.isfinite(value)
    except (TypeError, ValueError, OverflowError):
        return False


def _parse_number(value: object, field_name: str) -> float:
    """Parse file fields and report malformed numbers consistently as ValueError."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a finite number, got {value!r}")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field_name} must be a finite number, got {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be a finite number, got {value!r}")
    return number


def validate_problem(problem: KnapsackProblem) -> tuple[bool, str]:
    """Validates structural and numeric integrity of a KnapsackProblem instance.

    Args:
        problem: KnapsackProblem to inspect.

    Returns:
        A tuple of (is_valid: bool, message: str).
    """
    if not isinstance(problem, KnapsackProblem):
        return False, f"Expected KnapsackProblem, got {type(problem).__name__}"

    if not isinstance(problem.items, Sequence) or len(problem.items) < 1:
        return False, "Problem must contain a non-empty sequence of Items."

    if not _is_finite_number(problem.capacity) or problem.capacity <= 0.0:
        return False, f"Capacity must be a positive finite number, got {problem.capacity!r}"
    if not isinstance(problem.name, str):
        return False, "Problem name must be a string."

    for idx, item in enumerate(problem.items):
        if not isinstance(item, Item):
            return False, f"Item at index {idx} is not an Item instance."
        if not _is_finite_number(item.weight) or item.weight <= 0.0:
            return False, f"Item at index {idx} has invalid weight {item.weight!r}"
        if not _is_finite_number(item.value) or item.value < 0.0:
            return False, f"Item at index {idx} has invalid value {item.value!r}"
        if not isinstance(item.id, str):
            return False, f"Item at index {idx} has an invalid id."

    if tuple(problem.items) != tuple(problem):
        return False, "Problem items are inconsistent with its indexed items."

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
        n_items: Number of items to generate (integer >= 1, excluding bool).
        capacity_ratio: Knapsack capacity as a fraction of sum of all item weights (0.0 < ratio <= 1.0).
        min_weight: Minimum weight per item (> 0).
        max_weight: Maximum weight per item (>= min_weight).
        min_value: Minimum value per item (>= 0).
        max_value: Maximum value per item (>= min_value).
        seed: Integer seed for deterministic generation, or None.
        name: Name identifier for the generated problem.

    Returns:
        KnapsackProblem instance.

    Raises:
        ValueError: If arguments violate numeric requirements, or the resulting
            capacity cannot be represented as a positive finite float.
    """
    if isinstance(n_items, bool) or not isinstance(n_items, int) or n_items < 1:
        raise ValueError(f"n_items must be an integer >= 1, got {n_items!r}")
    if not _is_finite_number(capacity_ratio) or not (0.0 < capacity_ratio <= 1.0):
        raise ValueError(f"capacity_ratio must be finite and in (0.0, 1.0], got {capacity_ratio!r}")
    if (
        not _is_finite_number(min_weight) or not _is_finite_number(max_weight)
        or min_weight <= 0.0 or max_weight < min_weight
    ):
        raise ValueError(f"Invalid weight bounds: [{min_weight}, {max_weight}]")
    if (
        not _is_finite_number(min_value) or not _is_finite_number(max_value)
        or min_value < 0.0 or max_value < min_value
    ):
        raise ValueError(f"Invalid value bounds: [{min_value}, {max_value}]")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise ValueError("seed must be an integer or None.")
    if not isinstance(name, str):
        raise ValueError("name must be a string.")

    rng = random.Random(seed)
    items: list[Item] = []
    for idx in range(n_items):
        w = rng.uniform(min_weight, max_weight)
        v = rng.uniform(min_value, max_value)
        # Preserve valid small/narrow bounds when rounding would leave the range.
        if min_weight <= round(w, 2) <= max_weight:
            w = round(w, 2)
        if min_value <= round(v, 2) <= max_value:
            v = round(v, 2)
        items.append(Item(value=v, weight=w, id=f"item_{idx}"))

    capacity = sum(item.weight for item in items) * capacity_ratio
    if not math.isfinite(capacity) or capacity <= 0.0:
        raise ValueError("Generated capacity must be representable as a positive finite float.")

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

    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object.")

    name = data.get("name", path.stem)
    if "capacity" not in data:
        raise ValueError("JSON dataset missing required 'capacity' field.")

    capacity = _parse_number(data["capacity"], "capacity")
    items_raw = data.get("items")
    if not isinstance(items_raw, list) or len(items_raw) < 1:
        raise ValueError("JSON dataset must contain a non-empty 'items' list.")

    items: list[Item] = []
    for idx, raw in enumerate(items_raw):
        if not isinstance(raw, dict):
            raise ValueError(f"Item entry at index {idx} must be an object.")
        if "value" not in raw or "weight" not in raw:
            raise ValueError(f"Item at index {idx} must contain 'value' and 'weight'.")
        val = _parse_number(raw["value"], f"Item {idx} value")
        wt = _parse_number(raw["weight"], f"Item {idx} weight")
        item_id = raw.get("id", "")
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

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, strict=True)
        headers: list[str] = []
        col_indices: dict[str, int] = {}

        try:
            for row in reader:
                if not row or (len(row) == 1 and not row[0].strip()):
                    continue
                first_cell = row[0].strip()
                if first_cell.startswith("#"):
                    comment = ",".join(row).strip()[1:].strip()
                    label, separator, raw_capacity = comment.partition(":")
                    if label.strip().lower() == "capacity":
                        if not separator:
                            raise ValueError(f"Missing capacity value at CSV line {reader.line_num}.")
                        if capacity is not None:
                            raise ValueError("CSV dataset contains multiple capacity declarations.")
                        capacity = _parse_number(raw_capacity.strip(), "capacity")
                        if capacity <= 0.0:
                            raise ValueError("CSV capacity must be positive.")
                    continue

                if not headers:
                    headers = [h.strip().lower() for h in row]
                    if "value" not in headers or "weight" not in headers:
                        raise ValueError("CSV header must contain 'value' and 'weight' columns.")
                    if len(set(headers)) != len(headers):
                        raise ValueError("CSV header must not contain duplicate column names.")
                    col_indices = {header: index for index, header in enumerate(headers)}
                    continue

                if len(row) != len(headers):
                    raise ValueError(f"Wrong number of columns at CSV line {reader.line_num}: {row}")
                try:
                    val = _parse_number(row[col_indices["value"]].strip(), "value")
                    wt = _parse_number(row[col_indices["weight"]].strip(), "weight")
                    item_id = row[col_indices["id"]].strip() if "id" in col_indices else ""
                    items.append(Item(value=val, weight=wt, id=item_id))
                except ValueError as exc:
                    raise ValueError(f"Invalid item at CSV line {reader.line_num}: {exc}") from exc
        except csv.Error as exc:
            raise ValueError(f"Malformed CSV at line {reader.line_num}: {exc}") from exc

    if not items:
        raise ValueError("No items found in CSV dataset.")

    if capacity is None:
        capacity = sum(it.weight for it in items) * 0.5

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
