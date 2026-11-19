# 0/1 Knapsack Problem Solver: A* Search & Firefly Algorithm

Đồ án môn **Trí tuệ nhân tạo (Artificial Intelligence)**.  
**Hạn nộp:** 16/12/2026.

---

## 1. Giới thiệu đề tài

Dự án nghiên cứu, hiện thực hóa và so sánh thực nghiệm hai phương pháp giải bài toán tối ưu hóa tổ hợp kinh điển **0/1 Knapsack Problem**:
1. **A* Search (TV2):** Thuật toán tìm kiếm cây quyết định chính xác (Exact Search) kết hợp cắt tỉa cận trên (Branch-and-Bound pruning) dựa trên hàm thư giãn phân số (Fractional Knapsack relaxation). Đảm bảo tính admissible và tìm ra nghiệm tối ưu toàn cục.
2. **Firefly Algorithm (TV3):** Thuật toán tiến hóa bầy đàn (Swarm Intelligence Metaheuristic) mô phỏng hành vi phát sáng và thu hút của đom đóm. Sử dụng hàm Sigmoid ánh xạ không gian liên tục sang vectơ nhị phân kết hợp cơ chế sửa nghiệm vi phạm ràng buộc sức chứa (`repair_solution`).

---

## 2. Phân công trách nhiệm nhóm (4 thành viên)

| Thành viên | File chính phụ trách | Module & Nhiệm vụ chính |
| :--- | :--- | :--- |
| **TV1** | `core/*`, `docs/DATA.md`, `assets/datasets/*`, `tests/test_core.py` | Mô hình hóa dữ liệu bài toán (`Item`, `KnapsackProblem`), sinh/nạp dữ liệu (JSON/CSV), hàm đánh giá (`evaluate_binary_solution`), sửa nghiệm (`repair_solution`), tính cận trên (`compute_upper_bound`). |
| **TV2** | `algorithms/astar.py`, `main.py`, `requirements.txt`, `.gitignore`, `tests/test_astar.py`, `docs/INTERFACE_CONTRACT.md` | Thiết kế toán học & cài đặt thuật toán A* Search với Branch-and-Bound pruning, CLI entrypoint, quản lý contract và điều phối Git integration. |
| **TV3** | `algorithms/firefly.py`, `docs/SUMMARY.md`, `tests/test_firefly.py` | Cài đặt Firefly Algorithm với Sigmoid discretization, điều khiển siêu tham số (`FireflyConfig`), ghi nhận lịch sử hội tụ. |
| **TV4** | `gui/*`, `experiments/*`, `tests/test_integration.py`, `README.md` | Thiết kế giao diện trực quan `PySide6`, Worker chạy nền (`QThread`), khung thực nghiệm so sánh tự động (`benchmark.py`), tổng hợp báo cáo & slide. |

---

## 3. Cấu trúc thư mục dự án

```text
knapsack-ai-project/
├── main.py                     # Entry point chính của ứng dụng
├── requirements.txt            # Danh sách thư viện phụ thuộc
├── README.md                   # Hướng dẫn chi tiết
├── .gitignore                  # Cấu hình bỏ qua file rác và cache
├── core/                       # Package mô hình bài toán & đánh giá
│   ├── __init__.py
│   ├── knapsack.py             # Item, KnapsackProblem, SolutionResult
│   ├── dataset.py              # Đọc/ghi JSON, CSV và sinh dữ liệu ngẫu nhiên
│   └── evaluation.py           # evaluate, repair, compute_upper_bound
├── algorithms/                 # Package thuật toán AI
│   ├── __init__.py
│   ├── astar.py                # Thuật toán A* Search (TV2)
│   └── firefly.py              # Thuật toán Firefly Algorithm (TV3)
├── gui/                        # Giao diện đồ họa người dùng
│   ├── __init__.py
│   └── main_window.py          # PySide6 GUI & SolverWorker
├── experiments/                # Bộ công cụ thực nghiệm & benchmark
│   ├── __init__.py
│   ├── benchmark.py            # Chạy benchmark tự động & xuất CSV/JSON
│   └── results/                # Lưu trữ kết quả thực nghiệm
├── tests/                      # Bộ kiểm thử tự động
│   ├── __init__.py
│   ├── test_core.py            # Kiểm thử core module
│   ├── test_astar.py           # Kiểm thử A* contract
│   ├── test_firefly.py         # Kiểm thử Firefly contract
│   └── test_integration.py    # Kiểm thử tích hợp toàn hệ thống
├── docs/                       # Tài liệu đặc tả kỹ thuật
│   ├── INTERFACE_CONTRACT.md   # Bản hợp đồng giao diện chính thức
│   ├── DATA.md                 # Đặc tả cấu trúc dữ liệu
│   └── SUMMARY.md              # Bảng tóm tắt & so sánh thuật toán
└── assets/
    └── datasets/               # Các file dữ liệu mẫu (.json, .csv)
        ├── sample_01.json
        └── sample_01.csv
```

---

## 4. Hướng dẫn cài đặt & Chạy ứng dụng

### 4.1. Yêu cầu hệ thống
- Python `>= 3.10` (khuyến nghị Python 3.11 hoặc 3.12).
- Hệ điều hành: macOS, Linux, hoặc Windows.

### 4.2. Khởi tạo môi trường ảo (Virtual Environment)

```bash
# Di chuyển vào thư mục dự án
cd "knapsack-a*-firefly"

# Khởi tạo virtual environment
python3 -m venv .venv

# Kích hoạt virtual environment:
# Trên macOS / Linux:
source .venv/bin/activate
# Trên Windows (cmd / PowerShell):
# .venv\Scripts\activate
```

### 4.3. Cài đặt các thư viện cần thiết

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.4. Chạy chương trình

#### Chạy giao diện đồ họa GUI (PySide6):
```bash
python main.py
```
*(Nếu môi trường chưa cài đặt PySide6 hoặc chạy qua SSH/headless, chương trình sẽ tự động fallback sang chế độ CLI demo)*

---

## 5. Chạy bộ kiểm thử (Automated Tests)

Dự án hỗ trợ chạy test qua standard library `unittest` hoặc `pytest`:

```bash
# Chạy toàn bộ test bằng unittest
python3 -m unittest discover -s tests -v

# Hoặc nếu dùng pytest:
pytest tests/ -v
```

---

## 6. Luồng dữ liệu (Data Flow)

```text
[Input: UI Form / File JSON/CSV / Dataset Generator]
                         │
                         ▼
             [KnapsackProblem (core)]
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
 [solve_astar (TV2)]            [solve_firefly (TV3)]
         │                               │
         └───────────────┬───────────────┘
                         ▼
              [SolutionResult (core)]
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
[PySide6 Main Window (TV4)]    [Benchmark Summary (TV4)]
```

---

## 7. Quy định Git & Quy trình phối hợp nhóm

1. **Tuân thủ Interface Contract:** Mọi thay đổi trong `docs/INTERFACE_CONTRACT.md` phải được toàn nhóm thảo luận và phê duyệt trước khi cập nhật.
2. **Quy tắc tạo nhánh:**
   - TV1: `feature/core-dataset-eval`
   - TV2: `feature/astar-algorithm`
   - TV3: `feature/firefly-algorithm`
   - TV4: `feature/gui-benchmark`
3. **Quy tắc Commit & Review:**
   - Rebase nhánh của mình với `origin/main` trước khi tạo Pull Request:
     ```bash
     git fetch origin
     git rebase origin/main
     ```
   - Chạy kiểm thử nội bộ để đảm bảo 100% test pass trước khi yêu cầu review.
   - Mỗi Pull Request phải có ít nhất 2 thành viên review theo sơ đồ đã phân công:
     - TV1 review TV2, TV3.
     - TV2 review TV1, TV4.
     - TV3 review TV1, TV2.
     - TV4 review TV3, TV4.
