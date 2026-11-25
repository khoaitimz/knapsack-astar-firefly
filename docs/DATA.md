# ĐẶC TẢ DỮ LIỆU – 0/1 KNAPSACK PROBLEM

**Chủ sở hữu:** TV1

---

## 1. Mô hình dữ liệu chuẩn

### 1.1. Item (`core/knapsack.py`)
Mỗi vật phẩm được biểu diễn bởi class `Item`:
- `value: float` (hữu hạn, `>= 0.0`): Lợi ích thu được khi chọn vật phẩm.
- `weight: float` (hữu hạn, `> 0.0`): Trọng lượng vật phẩm chiếm dụng trong ba lô.
- `id: str` (tùy chọn): Định danh vật phẩm. Nếu để trống, tự động gán `"item_0"`, `"item_1"`...
- `density: float = value / weight`: Tỷ số mật độ giá trị/trọng lượng.

### 1.2. KnapsackProblem (`core/knapsack.py`)
Biểu diễn bài toán 0/1 Knapsack:
- `items: Sequence[Item]`: Tập hợp các vật phẩm khả dụng (`len >= 1`).
- `capacity: float` (hữu hạn, `> 0.0`): Sức chứa tối đa của ba lô.
- `name: str`: Tên bài toán (mặc định `"knapsack_01"`).

---

## 2. Định dạng lưu trữ dữ liệu

### 2.1. Định dạng JSON (`assets/datasets/*.json`)
```json
{
  "name": "sample_01",
  "capacity": 20.0,
  "items": [
    {"id": "item_a", "value": 24.0, "weight": 12.0},
    {"id": "item_b", "value": 13.0, "weight": 7.0},
    {"id": "item_c", "value": 23.0, "weight": 11.0},
    {"id": "item_d", "value": 15.0, "weight": 8.0}
  ]
}
```

### 2.2. Định dạng CSV (`assets/datasets/*.csv`)
```csv
# capacity: 20.0
id,value,weight
item_a,24.0,12.0
item_b,13.0,7.0
item_c,23.0,11.0
item_d,15.0,8.0
```

---

## 3. Sinh dữ liệu nhân tạo (`core/dataset.py`)
Hàm `generate_dataset(n_items, capacity_ratio, min_weight, max_weight, min_value, max_value, seed, name)`:
- `n_items`: Số lượng vật phẩm.
- `capacity_ratio`: Tỷ lệ sức chứa so với tổng trọng lượng (`0.0 < capacity_ratio <= 1.0`).
- `seed`: Giúp tái lập tập dữ liệu đồng nhất giữa các lần chạy.

`n_items` phải là số nguyên dương; `seed` là số nguyên hoặc `None`. Các khoảng
trọng lượng, giá trị và `capacity_ratio` phải hữu hạn; không chấp nhận `bool`.
Generator sử dụng bộ sinh số ngẫu nhiên riêng, không thay đổi trạng thái random
toàn cục. Giá trị và trọng lượng được làm tròn 2 chữ số khi kết quả vẫn nằm trong
khoảng yêu cầu. Sức chứa được tính bằng `sum(weights) * capacity_ratio`, không
làm tròn, để giữ đúng tỷ lệ với cả các trọng lượng rất nhỏ. Nếu sức chứa bị tràn
hoặc nhỏ đến mức trở thành 0 trong kiểu `float`, hàm báo `ValueError`.

## 4. Kiểm tra và nạp dữ liệu (`core/dataset.py`)

- `validate_problem(problem)` trả về `(True, message)` hoặc `(False, message)`;
  kiểm tra cấu trúc, kiểu dữ liệu, các giá trị hữu hạn và tính nhất quán giữa
  danh sách vật phẩm với cách truy cập theo chỉ số.
- `load_dataset_json(file_path)` yêu cầu `capacity` và danh sách `items` không
  rỗng; mỗi vật phẩm phải có `value`, `weight`. `name` mặc định là tên file
  không có phần mở rộng; `id` bỏ trống được tự động gán theo chỉ số.
- `load_dataset_csv(file_path)` yêu cầu các cột `value`, `weight`; `id` là tùy
  chọn. Thứ tự cột có thể thay đổi. Nếu không khai báo `# capacity: <value>`,
  sức chứa mặc định bằng `0.5 * sum(weights)`. Khai báo sức chứa sai hoặc lặp
  lại, tên cột trùng và dòng sai số cột đều bị từ chối.
- Hai loader hỗ trợ UTF-8 có hoặc không có BOM, chấp nhận chuỗi số hợp lệ,
  từ chối `bool`, `null`, NaN và vô cực trong trường số. File thiếu báo
  `FileNotFoundError`; nội dung sai báo `ValueError`.
