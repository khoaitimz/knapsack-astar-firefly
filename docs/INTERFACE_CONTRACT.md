# INTERFACE CONTRACT – KNAPSACK AI PROJECT (A* & FIREFLY ALGORITHM)

## 1. Cấu trúc thư mục thống nhất
- `main.py` (TV2)
- `requirements.txt` (TV2), `README.md` (TV4), `.gitignore` (TV2)
- `core/`: `__init__.py` (TV1), `knapsack.py` (TV1), `dataset.py` (TV1), `evaluation.py` (TV1)
- `algorithms/`: `__init__.py` (TV2), `astar.py` (TV2), `firefly.py` (TV3)
- `gui/`: `__init__.py` (TV4), `main_window.py` (TV4)
- `experiments/`: `__init__.py` (TV4), `benchmark.py` (TV4), `results/` (TV4)
- `tests/`: `__init__.py` (TV2), `test_core.py` (TV1), `test_astar.py` (TV2), `test_firefly.py` (TV3), `test_integration.py` (TV4)
- `docs/`: `INTERFACE_CONTRACT.md` (TV2), `DATA.md` (TV1), `SUMMARY.md` (TV3)
- `assets/datasets/` (TV1)

## 2. Class và kiểu dữ liệu dùng chung (`core/knapsack.py`)
- `Item(value: float, weight: float, id: str = "")`:
  - `weight > 0.0` (hữu hạn), `value >= 0.0` (hữu hạn); sai raise `ValueError`.
- `KnapsackProblem(items: Sequence[Item], capacity: float, name: str = "knapsack_01")`:
  - `len(items) >= 1`, `capacity > 0.0` (hữu hạn); sai raise `ValueError`.
  - Nếu `item.id == ""`, gán tự động `"item_0"`, `"item_1"`, ... theo chỉ số.
- `SolutionResult(algorithm_name: str, selected_indices: list[int], binary_vector: list[int], total_value: float, total_weight: float, is_feasible: bool, execution_time_ms: float, status: str, metrics: dict[str, float | int | list[float]])`:
  - `status` thuộc `{"optimal", "feasible", "time_limit", "max_iter", "max_expanded", "no_feasible_solution"}`.

## 3. Chữ ký hàm chuẩn
- `core/dataset.py`:
  - `validate_problem(problem: KnapsackProblem) -> tuple[bool, str]`
  - `generate_dataset(n_items: int, capacity_ratio: float = 0.5, min_weight: float = 1.0, max_weight: float = 20.0, min_value: float = 1.0, max_value: float = 50.0, seed: int | None = None, name: str = "synthetic") -> KnapsackProblem`
  - `load_dataset_json(file_path: str) -> KnapsackProblem`
  - `load_dataset_csv(file_path: str) -> KnapsackProblem`
- `core/evaluation.py`:
  - `evaluate_binary_solution(problem: KnapsackProblem, binary_vector: list[int] | tuple[int, ...]) -> tuple[float, float, bool]`
  - `repair_solution(problem: KnapsackProblem, binary_vector: list[int] | tuple[int, ...], strategy: str = "density_asc") -> list[int]`
  - `compute_upper_bound(problem: KnapsackProblem, start_index: int, remaining_capacity: float, sorted_indices: tuple[int, ...] | None = None) -> float`
    *(Trả về `remaining_fractional_gain`: phần giá trị cộng thêm tối đa từ `start_index` trở đi với sức chứa còn lại `remaining_capacity`, chưa bao gồm `current_value`.)*
- `algorithms/astar.py`:
  - `solve_astar(problem: KnapsackProblem, time_limit_sec: float = 5.0, max_expanded_nodes: int = 100_000) -> SolutionResult`
- `algorithms/firefly.py`:
  - `FireflyConfig(population_size: int = 20, max_iterations: int = 100, alpha: float = 0.5, alpha_decay: float = 0.98, beta0: float = 1.0, gamma: float = 1.0, coord_min: float = -6.0, coord_max: float = 6.0, time_limit_sec: float = 5.0, seed: int | None = 42)`
  - `solve_firefly(problem: KnapsackProblem, config: FireflyConfig | None = None) -> SolutionResult`
- `experiments/benchmark.py`:
  - `run_benchmark(problems: list[KnapsackProblem], firefly_config: FireflyConfig | None = None, fa_runs: int = 5, astar_time_limit_sec: float = 5.0, astar_max_expanded_nodes: int = 100_000) -> list[dict[str, float | int | str | bool]]`
  - `export_benchmark_results(records: list[dict[str, float | int | str | bool]], output_dir: str = "experiments/results") -> dict[str, str]`

## 4. Quy ước tên biến và kiểu dữ liệu
- `snake_case` cho biến, hàm, tham số, tên file; `PascalCase` cho class.
- Giá trị, trọng lượng, sức chứa, cận trên, thời gian dùng `float`; chỉ số vật phẩm, bit nhị phân (`0`/`1`), số vòng lặp/nút dùng `int`.

## 5. Quy tắc xử lý lỗi
- Đầu vào/file không hợp lệ raise `ValueError` hoặc `FileNotFoundError`.
- Chạm giới hạn thời gian hoặc số nút/vòng lặp: trả về `SolutionResult` với nghiệm tốt nhất hiện có và `status` tương ứng (`"time_limit"`, `"max_expanded"`, `"max_iter"`).

## 6. Quy ước import giữa các package
- `core/*` -> chỉ thư viện chuẩn và nội bộ `core/`.
- `algorithms/*` -> `core.*` và thư viện chuẩn/`numpy`/`math`/`heapq`/`time`; không import `gui` hoặc `experiments`.
- `experiments/*` và `gui/*` -> được import `core.*` và `algorithms.*`.

## 7. Luồng dữ liệu từ đầu vào đến đầu ra
Form / File / Generator -> `KnapsackProblem` -> `solve_astar` & `solve_firefly` (sử dụng `core/evaluation.py`) -> `SolutionResult` -> `run_benchmark` / `SolverWorker` -> `KnapsackMainWindow` & `experiments/results/`.

## 8. Ví dụ tích hợp chuẩn
```python
from core.knapsack import Item, KnapsackProblem
from algorithms.astar import solve_astar
from algorithms.firefly import FireflyConfig, solve_firefly
from experiments.benchmark import run_benchmark

problem = KnapsackProblem(
    items=[
        Item(value=24.0, weight=12.0, id="item_a"),
        Item(value=13.0, weight=7.0, id="item_b"),
        Item(value=23.0, weight=11.0, id="item_c"),
        Item(value=15.0, weight=8.0, id="item_d"),
    ],
    capacity=20.0,
    name="sample_01",
)
astar_res = solve_astar(problem, time_limit_sec=5.0, max_expanded_nodes=100_000)
fa_res = solve_firefly(problem, FireflyConfig(population_size=20, max_iterations=100, seed=42))
benchmark_rows = run_benchmark(
    problems=[problem],
    firefly_config=FireflyConfig(population_size=20, max_iterations=100, seed=42),
    fa_runs=3,
    astar_time_limit_sec=5.0,
    astar_max_expanded_nodes=100_000,
)
```
