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
